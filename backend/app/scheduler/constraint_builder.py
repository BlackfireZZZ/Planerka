"""
Module for building constraints from database data.
"""

from typing import Dict, List, Set
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    ClassGroup,
    Constraint,
    Institution,
    Lesson,
    Room,
    Student,
    StudyGroup,
    Teacher,
    TeacherLesson,
    TimeSlot,
)
from app.db.models.study_group import study_group_student


class ConstraintBuilder:
    """
    Class for building constraints from database data.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_from_institution(self, institution_id: UUID) -> Dict:
        """
        Loads all institution data and builds structure for schedule generation.

        Args:
            institution_id: Institution ID

        Returns:
            Dictionary with data:
            {
                "lessons": [...],
                "teachers": [...],
                "class_groups": [...],
                "study_groups": [...],
                "rooms": [...],
                "time_slots": [...],
                "teacher_lessons": {...},
                "room_capacities": {...},
                "class_group_sizes": {...},
                "study_group_sizes": {...},
                "student_group_memberships": {...},
                "constraints": [...]
            }
        """
        lessons_result = await self.db.execute(
            select(Lesson).where(Lesson.institution_id == institution_id)
        )
        lessons = lessons_result.scalars().all()

        teachers_result = await self.db.execute(
            select(Teacher).where(Teacher.institution_id == institution_id)
        )
        teachers = teachers_result.scalars().all()

        class_groups_result = await self.db.execute(
            select(ClassGroup).where(ClassGroup.institution_id == institution_id)
        )
        class_groups = class_groups_result.scalars().all()

        rooms_result = await self.db.execute(
            select(Room).where(Room.institution_id == institution_id)
        )
        rooms = rooms_result.scalars().all()

        time_slots_result = await self.db.execute(
            select(TimeSlot).where(TimeSlot.institution_id == institution_id)
        )
        time_slots = time_slots_result.scalars().all()
        teacher_lessons_dict: Dict[int, Set[UUID]] = {}
        for teacher in teachers:
            teacher_lessons_result = await self.db.execute(
                select(TeacherLesson).where(TeacherLesson.teacher_id == teacher.id)
            )
            teacher_lessons = teacher_lessons_result.scalars().all()
            teacher_lessons_dict[teacher.id] = {tl.lesson_id for tl in teacher_lessons}
        constraints_result = await self.db.execute(
            select(Constraint).where(Constraint.institution_id == institution_id)
        )
        constraints = constraints_result.scalars().all()
        study_groups_result = await self.db.execute(
            select(StudyGroup).where(StudyGroup.institution_id == institution_id)
        )
        study_groups = study_groups_result.scalars().all()
        room_capacities = {room.id: room.capacity for room in rooms}
        class_group_sizes = {cg.id: cg.student_count for cg in class_groups}
        study_group_sizes = {}
        student_group_memberships: Dict[UUID, Dict] = {}

        for study_group in study_groups:
            result = await self.db.execute(
                select(Student)
                .join(study_group_student)
                .where(study_group_student.c.study_group_id == study_group.id)
            )
            students = result.scalars().all()
            study_group_sizes[study_group.id] = len(students)
            for student in students:
                if student.id not in student_group_memberships:
                    student_group_memberships[student.id] = {
                        "class_group_id": student.class_group_id,
                        "study_group_ids": [],
                    }
                student_group_memberships[student.id]["study_group_ids"].append(
                    study_group.id
                )
        constraints_list = []
        for constraint in constraints:
            constraints_list.append(
                {
                    "constraint_type": constraint.constraint_type,
                    "constraint_data": constraint.constraint_data,
                    "priority": constraint.priority,
                }
            )

        return {
            "lessons": [lesson.id for lesson in lessons],
            "teachers": [teacher.id for teacher in teachers],
            "class_groups": [cg.id for cg in class_groups],
            "study_groups": [sg.id for sg in study_groups],
            "rooms": [room.id for room in rooms],
            "time_slots": [ts.id for ts in time_slots],
            "teacher_lessons": teacher_lessons_dict,
            "room_capacities": room_capacities,
            "class_group_sizes": class_group_sizes,
            "study_group_sizes": study_group_sizes,
            "student_group_memberships": student_group_memberships,
            "constraints": constraints_list,
        }

    async def build_teacher_availability(
        self, institution_id: UUID
    ) -> Dict[int, List[UUID]]:
        """
        Builds dictionary of teacher availability.

        Returns:
            {teacher_id: [available_time_slot_ids]}
        """
        constraints_result = await self.db.execute(
            select(Constraint).where(
                Constraint.institution_id == institution_id,
                Constraint.constraint_type == "teacher_unavailable",
            )
        )
        constraints = constraints_result.scalars().all()
        time_slots_result = await self.db.execute(
            select(TimeSlot).where(TimeSlot.institution_id == institution_id)
        )
        all_time_slots = {ts.id for ts in time_slots_result.scalars().all()}
        teachers_result = await self.db.execute(
            select(Teacher).where(Teacher.institution_id == institution_id)
        )
        teachers = teachers_result.scalars().all()

        availability: Dict[int, List[UUID]] = {}
        for teacher in teachers:
            unavailable_slots = set()
            for constraint in constraints:
                constraint_data = constraint.constraint_data
                if constraint_data.get("teacher_id") == teacher.id:
                    unavailable_slots.update(constraint_data.get("time_slot_ids", []))

            available_slots = all_time_slots - unavailable_slots
            availability[teacher.id] = list(available_slots)

        return availability

    async def build_room_availability(
        self, institution_id: UUID
    ) -> Dict[UUID, List[UUID]]:
        """
        Builds dictionary of room availability.

        Returns:
            {room_id: [available_time_slot_ids]}
        """
        constraints_result = await self.db.execute(
            select(Constraint).where(
                Constraint.institution_id == institution_id,
                Constraint.constraint_type == "room_unavailable",
            )
        )
        constraints = constraints_result.scalars().all()

        time_slots_result = await self.db.execute(
            select(TimeSlot).where(TimeSlot.institution_id == institution_id)
        )
        all_time_slots = {ts.id for ts in time_slots_result.scalars().all()}

        rooms_result = await self.db.execute(
            select(Room).where(Room.institution_id == institution_id)
        )
        rooms = rooms_result.scalars().all()

        availability: Dict[UUID, List[UUID]] = {}
        for room in rooms:
            unavailable_slots = set()
            for constraint in constraints:
                constraint_data = constraint.constraint_data
                if constraint_data.get("room_id") == room.id:
                    unavailable_slots.update(constraint_data.get("time_slot_ids", []))

            available_slots = all_time_slots - unavailable_slots
            availability[room.id] = list(available_slots)

        return availability

    async def build_class_preferences(self, institution_id: UUID) -> Dict[UUID, Dict]:
        """
        Builds dictionary of class preferences.

        Returns:
            {class_group_id: {preferences}}
        """
        constraints_result = await self.db.execute(
            select(Constraint).where(
                Constraint.institution_id == institution_id,
                Constraint.constraint_type == "class_preference",
            )
        )
        constraints = constraints_result.scalars().all()

        preferences: Dict[UUID, Dict] = {}
        for constraint in constraints:
            constraint_data = constraint.constraint_data
            class_group_id = constraint_data.get("class_group_id")
            if class_group_id:
                preferences[class_group_id] = constraint_data

        return preferences
