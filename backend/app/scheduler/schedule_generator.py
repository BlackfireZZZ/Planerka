"""
Main class for schedule generation.
"""

from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.scheduler.constraint_builder import ConstraintBuilder
from app.scheduler.sat_encoder import ScheduleEncoder
from app.scheduler.sat_solver import ScheduleSolver


class ScheduleGenerator:
    """
    Main class for schedule generation using SAT solver.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.constraint_builder = ConstraintBuilder(db)

    async def validate_input(self, institution_id: UUID) -> tuple[bool, Optional[str]]:
        """
        Validates input data before schedule generation.

        Args:
            institution_id: Institution ID

        Returns:
            (is_valid, error_message)
        """
        data = await self.constraint_builder.build_from_institution(institution_id)
        if not data["lessons"]:
            return False, "No lessons found for this institution"
        if not data["teachers"]:
            return False, "No teachers found for this institution"
        if not data["class_groups"] and not data.get("study_groups"):
            return False, "No class groups or study groups found for this institution"
        if not data["rooms"]:
            return False, "No rooms found for this institution"
        if not data["time_slots"]:
            return False, "No time slots found for this institution"
        teachers_with_lessons = {
            t_id for t_id, lessons in data["teacher_lessons"].items() if lessons
        }
        if not teachers_with_lessons:
            return False, "No teachers have assigned lessons"
        min_required_slots = len(data["lessons"])
        if len(data["time_slots"]) < min_required_slots:
            return (
                False,
                f"Not enough time slots. Required: {min_required_slots}, Available: {len(data['time_slots'])}",
            )

        return True, None

    async def generate(
        self, institution_id: UUID, timeout: int = 300
    ) -> tuple[bool, Optional[List[Dict]], Optional[str]]:
        """
        Generates schedule for an institution.

        Args:
            institution_id: Institution ID
            timeout: Maximum solving time in seconds

        Returns:
            (success, schedule_entries, error_message)
            schedule_entries: List of dictionaries with fields:
                {
                    "lesson_id": UUID,
                    "teacher_id": int,
                    "class_group_id": UUID | None,
                    "study_group_id": UUID | None,
                    "room_id": UUID,
                    "time_slot_id": UUID
                }
        """
        is_valid, error = await self.validate_input(institution_id)
        if not is_valid:
            return False, None, error
        data = await self.constraint_builder.build_from_institution(institution_id)
        encoder = ScheduleEncoder()
        study_groups = data.get("study_groups", [])
        encoder.encode_variables(
            lessons=data["lessons"],
            teachers=data["teachers"],
            class_groups=data["class_groups"],
            study_groups=study_groups,
            rooms=data["rooms"],
            time_slots=data["time_slots"],
            teacher_lessons=data["teacher_lessons"],
        )
        encoder.encode_hard_constraints(
            lessons=data["lessons"],
            class_groups=data["class_groups"],
            study_groups=study_groups,
            teachers=data["teachers"],
            rooms=data["rooms"],
            time_slots=data["time_slots"],
            room_capacities=data["room_capacities"],
            class_group_sizes=data["class_group_sizes"],
            study_group_sizes=data.get("study_group_sizes", {}),
            student_group_memberships=data.get("student_group_memberships", {}),
        )
        encoder.encode_custom_constraints(data["constraints"])
        with ScheduleSolver(encoder) as solver:
            if solver.solve(timeout=timeout):
                schedule = solver.extract_schedule()
                schedule_entries = []
                group_types = encoder.group_types
                for (
                    lesson_id,
                    teacher_id,
                    group_id,
                    room_id,
                    time_slot_id,
                ) in schedule:
                    group_type = group_types.get(group_id, "class_group")
                    entry = {
                        "lesson_id": lesson_id,
                        "teacher_id": teacher_id,
                        "room_id": room_id,
                        "time_slot_id": time_slot_id,
                    }
                    if group_type == "class_group":
                        entry["class_group_id"] = group_id
                        entry["study_group_id"] = None
                    else:
                        entry["class_group_id"] = None
                        entry["study_group_id"] = group_id
                    schedule_entries.append(entry)

                return True, schedule_entries, None
            else:
                return (
                    False,
                    None,
                    "No solution found. Constraints may be too restrictive.",
                )

    async def apply_constraints(
        self, institution_id: UUID, constraints: List[Dict]
    ) -> Dict:
        """
        Applies additional constraints.

        Args:
            institution_id: Institution ID
            constraints: List of constraints

        Returns:
            Updated data with applied constraints
        """
        data = await self.constraint_builder.build_from_institution(institution_id)
        data["constraints"].extend(constraints)
        return data
