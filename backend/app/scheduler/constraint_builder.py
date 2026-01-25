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
from app.db.models.class_group import class_group_lessons
from app.db.models.study_group import study_group_lessons, study_group_student


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
        teacher_lessons_dict: Dict[int, Set[UUID]] = {t.id: set() for t in teachers}
        if teachers:
            tl_result = await self.db.execute(
                select(TeacherLesson).where(
                    TeacherLesson.teacher_id.in_([t.id for t in teachers])
                )
            )
            for tl in tl_result.scalars().all():
                teacher_lessons_dict[tl.teacher_id].add(tl.lesson_id)
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

        class_group_lessons_dict: Dict[UUID, Dict[UUID, int]] = {}
        if class_groups:
            cg_lessons_result = await self.db.execute(
                select(class_group_lessons).where(
                    class_group_lessons.c.class_group_id.in_(
                        [cg.id for cg in class_groups]
                    )
                )
            )
            for row in cg_lessons_result.all():
                cg_id = row.class_group_id
                if cg_id not in class_group_lessons_dict:
                    class_group_lessons_dict[cg_id] = {}
                class_group_lessons_dict[cg_id][row.lesson_id] = row._mapping["count"]

        study_group_lessons_dict: Dict[UUID, Dict[UUID, int]] = {}
        if study_groups:
            sg_lessons_result = await self.db.execute(
                select(study_group_lessons).where(
                    study_group_lessons.c.study_group_id.in_(
                        [sg.id for sg in study_groups]
                    )
                )
            )
            for row in sg_lessons_result.all():
                sgg_id = row.study_group_id
                if sgg_id not in study_group_lessons_dict:
                    study_group_lessons_dict[sgg_id] = {}
                study_group_lessons_dict[sgg_id][row.lesson_id] = row._mapping["count"]

        if study_groups:
            sg_ids = [sg.id for sg in study_groups]
            sg_students_result = await self.db.execute(
                select(Student, study_group_student.c.study_group_id)
                .select_from(Student)
                .join(study_group_student, Student.id == study_group_student.c.student_id)
                .where(study_group_student.c.study_group_id.in_(sg_ids))
            )
            sg_to_students: Dict[UUID, List[Student]] = {sg.id: [] for sg in study_groups}
            for student, sg_id in sg_students_result.all():
                sg_to_students[sg_id].append(student)
            for sg in study_groups:
                students = sg_to_students.get(sg.id, [])
                study_group_sizes[sg.id] = len(students)
                for student in students:
                    if student.id not in student_group_memberships:
                        student_group_memberships[student.id] = {
                            "class_group_id": student.class_group_id,
                            "study_group_ids": [],
                        }
                    student_group_memberships[student.id]["study_group_ids"].append(
                        sg.id
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
            "class_group_lessons": class_group_lessons_dict,
            "study_group_lessons": study_group_lessons_dict,
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
