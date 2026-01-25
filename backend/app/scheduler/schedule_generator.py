"""
Main class for schedule generation.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.scheduler.constraint_builder import ConstraintBuilder
from app.scheduler.sat_encoder import ScheduleEncoder
from app.scheduler.sat_solver import ScheduleSolver

logger = logging.getLogger(__name__)


def _serialize_for_debug_log(obj: Any) -> Any:
    """Convert input data to JSON-serializable form for debug logging."""
    if obj is None:
        return None
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, (int, float, str, bool)):
        return obj
    if isinstance(obj, set):
        return [_serialize_for_debug_log(x) for x in obj]
    if isinstance(obj, list):
        return [_serialize_for_debug_log(x) for x in obj]
    if isinstance(obj, dict):
        return {
            (str(k) if isinstance(k, UUID) else k): _serialize_for_debug_log(v)
            for k, v in obj.items()
        }
    return str(obj)


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

        class_group_lessons = data.get("class_group_lessons", {})
        study_group_lessons = data.get("study_group_lessons", {})
        total_slots = sum(
            c for d in class_group_lessons.values() for c in d.values()
        ) + sum(c for d in study_group_lessons.values() for c in d.values())
        if total_slots == 0:
            return (
                False,
                "No lesson–group assignments. Assign lessons to class groups and/or "
                "study groups in the Group Lessons tab.",
            )
        at_least_one_teachable = False
        for cg_id, lessons_dict in class_group_lessons.items():
            for lid in lessons_dict:
                if any(
                    lid in data["teacher_lessons"].get(tid, set())
                    for tid in teachers_with_lessons
                ):
                    at_least_one_teachable = True
                    break
            if at_least_one_teachable:
                break
        if not at_least_one_teachable:
            for sg_id, lessons_dict in study_group_lessons.items():
                for lid in lessons_dict:
                    if any(
                        lid in data["teacher_lessons"].get(tid, set())
                        for tid in teachers_with_lessons
                    ):
                        at_least_one_teachable = True
                        break
                if at_least_one_teachable:
                    break
        if not at_least_one_teachable:
            return (
                False,
                "No lesson–group assignments with an assigned teacher. Assign lessons to "
                "class groups and/or study groups in the Group Lessons tab, and ensure "
                "those lessons are assigned to at least one teacher.",
            )

        # Multiple (lesson, group) pairs can share a time slot when there is no
        # resource conflict (different teacher, room, no student overlap).
        # So we only require at least one time slot; "No time slots" is checked above.
        # We do not require time_slots >= total_pairs.

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

        # --- ВРЕМЕННОЕ ЛОГИРОВАНИЕ: входные данные перед генерацией (удалить после отладки) ---
        _debug_payload = {
            "institution_id": str(institution_id),
            "timeout": timeout,
            "data": data,
        }
        _debug_serialized = _serialize_for_debug_log(_debug_payload)
        _debug_path = (
            Path(__file__).resolve().parent.parent.parent
            / "schedule_generation_input_debug.json"
        )
        try:
            with open(_debug_path, "w", encoding="utf-8") as f:
                json.dump(_debug_serialized, f, ensure_ascii=False, indent=2)
            logger.info("Schedule generation input logged to %s", _debug_path)
        except Exception as e:
            logger.warning("Could not write schedule input debug file: %s", e)
        # --- конец временного логирования ---

        encoder = ScheduleEncoder()
        study_groups = data.get("study_groups", [])
        class_group_lessons = data.get("class_group_lessons", {})
        study_group_lessons = data.get("study_group_lessons", {})
        encoder.encode_variables(
            lessons=data["lessons"],
            teachers=data["teachers"],
            class_groups=data["class_groups"],
            study_groups=study_groups,
            rooms=data["rooms"],
            time_slots=data["time_slots"],
            teacher_lessons=data["teacher_lessons"],
            class_group_lessons=class_group_lessons,
            study_group_lessons=study_group_lessons,
        )
        infeasible = encoder.get_infeasible_pairs(
            class_group_lessons=class_group_lessons,
            study_group_lessons=study_group_lessons,
            room_capacities=data["room_capacities"],
            class_group_sizes=data["class_group_sizes"],
            study_group_sizes=data.get("study_group_sizes", {}),
        )
        if infeasible:
            parts = [f"lesson {l} group {g}: {r}" for l, g, r in infeasible]
            return False, None, "Infeasible: " + "; ".join(parts)
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
            class_group_lessons=class_group_lessons,
            study_group_lessons=study_group_lessons,
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
                # Diagnostic: can assignments be made without pairwise conflicts?
                diag = ScheduleEncoder()
                diag.encode_variables(
                    lessons=data["lessons"],
                    teachers=data["teachers"],
                    class_groups=data["class_groups"],
                    study_groups=study_groups,
                    rooms=data["rooms"],
                    time_slots=data["time_slots"],
                    teacher_lessons=data["teacher_lessons"],
                    class_group_lessons=class_group_lessons,
                    study_group_lessons=study_group_lessons,
                )
                diag.encode_hard_constraints(
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
                    class_group_lessons=class_group_lessons,
                    study_group_lessons=study_group_lessons,
                    skip_conflicts=True,
                )
                diag.encode_custom_constraints(data["constraints"])
                with ScheduleSolver(diag) as diag_solver:
                    if diag_solver.solve(timeout=timeout):
                        return (
                            False,
                            None,
                            "No solution: resource conflicts make the schedule impossible "
                            "(teacher, room, or student overlap in at least one time slot). "
                            "Try: more time slots, more teachers, or more rooms.",
                        )
                    else:
                        return (
                            False,
                            None,
                            "No solution: some (lesson, group) pairs have no valid "
                            "(teacher, room, time slot) after room capacity and "
                            "teacher/room unavailability. Check room capacity and "
                            "teacher/room availability constraints.",
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
