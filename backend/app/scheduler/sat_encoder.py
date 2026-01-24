"""
Module for converting schedule constraints to CNF formula.
"""

from typing import Dict, List, Set, Tuple
from uuid import UUID

from pysat.formula import CNF
from pysat.solvers import Solver


class ScheduleEncoder:
    """
    Class for converting schedule constraints to CNF formula.

    Creates boolean variables for each possible combination:
    (lesson, teacher, class_group, room, time_slot)
    """

    def __init__(self):
        self.variables: Dict[Tuple[UUID, int, UUID, UUID, UUID], int] = {}
        self.reverse_variables: Dict[int, Tuple[UUID, int, UUID, UUID, UUID]] = {}
        self.group_types: Dict[UUID, str] = {}  # {group_id: "class_group" | "study_group"}
        self.next_var = 1
        self.cnf = CNF()

    def encode_variables(
        self,
        lessons: List[UUID],
        teachers: List[int],
        class_groups: List[UUID],
        study_groups: List[UUID],
        rooms: List[UUID],
        time_slots: List[UUID],
        teacher_lessons: Dict[int, Set[UUID]],
    ) -> None:
        """
        Creates boolean variables for all possible combinations.

        Args:
            lessons: List of lesson IDs
            teachers: List of teacher IDs
            class_groups: List of class group IDs
            study_groups: List of study group IDs
            rooms: List of room IDs
            time_slots: List of time slot IDs
            teacher_lessons: Dictionary {teacher_id: set(lesson_ids)} - which lessons a teacher can teach
        """
        # Track group types
        for cg_id in class_groups:
            self.group_types[cg_id] = "class_group"
        for sg_id in study_groups:
            self.group_types[sg_id] = "study_group"

        all_groups = class_groups + study_groups

        for lesson_id in lessons:
            for teacher_id in teachers:
                # Check if teacher can teach this lesson
                if lesson_id not in teacher_lessons.get(teacher_id, set()):
                    continue

                for group_id in all_groups:
                    for room_id in rooms:
                        for time_slot_id in time_slots:
                            key = (
                                lesson_id,
                                teacher_id,
                                group_id,
                                room_id,
                                time_slot_id,
                            )
                            if key not in self.variables:
                                self.variables[key] = self.next_var
                                self.reverse_variables[self.next_var] = key
                                self.next_var += 1

    def encode_hard_constraints(
        self,
        lessons: List[UUID],
        class_groups: List[UUID],
        study_groups: List[UUID],
        teachers: List[int],
        rooms: List[UUID],
        time_slots: List[UUID],
        room_capacities: Dict[UUID, int],
        class_group_sizes: Dict[UUID, int],
        study_group_sizes: Dict[UUID, int],
        student_group_memberships: Dict[UUID, Dict],
    ) -> None:
        """
        Encodes mandatory constraints (hard constraints).

        Hard constraints:
        1. Each lesson must be assigned exactly once
        2. Teacher cannot be in two places at the same time
        3. Class cannot be in two places at the same time
        4. Room cannot be occupied by two lessons simultaneously
        5. Teacher must teach only their subjects (already checked in encode_variables)
        6. Room must have sufficient capacity
        """
        # 1. Each lesson must be assigned exactly once
        for lesson_id in lessons:
            lesson_vars = [
                var
                for (l_id, t_id, cg_id, r_id, ts_id), var in self.variables.items()
                if l_id == lesson_id
            ]
            if lesson_vars:
                # At least one
                self.cnf.append(lesson_vars)
                # At most one - for each pair of variables add negation
                for i in range(len(lesson_vars)):
                    for j in range(i + 1, len(lesson_vars)):
                        self.cnf.append([-lesson_vars[i], -lesson_vars[j]])

        # 2. Teacher cannot be in two places at the same time (in one time slot)
        for teacher_id in teachers:
            for time_slot_id in time_slots:
                teacher_time_vars = [
                    var
                    for (l_id, t_id, cg_id, r_id, ts_id), var in self.variables.items()
                    if t_id == teacher_id and ts_id == time_slot_id
                ]
                # At most one
                for i in range(len(teacher_time_vars)):
                    for j in range(i + 1, len(teacher_time_vars)):
                        self.cnf.append([-teacher_time_vars[i], -teacher_time_vars[j]])

        # 3. Class/Study group cannot be in two places at the same time
        all_groups = class_groups + study_groups
        for group_id in all_groups:
            for time_slot_id in time_slots:
                group_time_vars = [
                    var
                    for (l_id, t_id, g_id, r_id, ts_id), var in self.variables.items()
                    if g_id == group_id and ts_id == time_slot_id
                ]
                # At most one
                for i in range(len(group_time_vars)):
                    for j in range(i + 1, len(group_time_vars)):
                        self.cnf.append([-group_time_vars[i], -group_time_vars[j]])

        # 3b. Students cannot be in two places at the same time
        # If a student is in both a class group and study groups, they can't have overlapping schedules
        for student_id, memberships in student_group_memberships.items():
            class_group_id = memberships.get("class_group_id")
            study_group_ids = memberships.get("study_group_ids", [])
            
            if class_group_id and study_group_ids:
                # Student is in a class group and study groups
                # They can't have overlapping time slots
                for study_group_id in study_group_ids:
                    for time_slot_id in time_slots:
                        # Get all variables for class group at this time
                        class_vars = [
                            var
                            for (l_id, t_id, g_id, r_id, ts_id), var in self.variables.items()
                            if g_id == class_group_id and ts_id == time_slot_id
                        ]
                        # Get all variables for study group at this time
                        study_vars = [
                            var
                            for (l_id, t_id, g_id, r_id, ts_id), var in self.variables.items()
                            if g_id == study_group_id and ts_id == time_slot_id
                        ]
                        # Student can't be in both at the same time
                        for class_var in class_vars:
                            for study_var in study_vars:
                                self.cnf.append([-class_var, -study_var])

        # 4. Room cannot be occupied by two lessons simultaneously
        for room_id in rooms:
            for time_slot_id in time_slots:
                room_time_vars = [
                    var
                    for (l_id, t_id, cg_id, r_id, ts_id), var in self.variables.items()
                    if r_id == room_id and ts_id == time_slot_id
                ]
                # At most one
                for i in range(len(room_time_vars)):
                    for j in range(i + 1, len(room_time_vars)):
                        self.cnf.append([-room_time_vars[i], -room_time_vars[j]])

        # 6. Room must have sufficient capacity
        for (l_id, t_id, g_id, r_id, ts_id), var in self.variables.items():
            room_capacity = room_capacities.get(r_id, 0)
            group_type = self.group_types.get(g_id, "class_group")
            if group_type == "class_group":
                group_size = class_group_sizes.get(g_id, 0)
            else:
                group_size = study_group_sizes.get(g_id, 0)
            if group_size > room_capacity:
                # If group doesn't fit in room, forbid this combination
                self.cnf.append([-var])

    def encode_soft_constraints(
        self,
        preferences: Dict[str, List[Tuple[UUID, int, UUID, UUID, UUID]]],
    ) -> None:
        """
        Encodes desirable constraints (soft constraints).

        Soft constraints are added as additional clauses that are desirable to satisfy,
        but not mandatory. In the current implementation they are added as regular clauses,
        but with lower priority (can use MAX-SAT solver for optimization).

        Args:
            preferences: Dictionary of preferences, e.g.:
                {"no_gaps": [(lesson_id, teacher_id, class_id, room_id, time_slot_id), ...]}
        """
        # Minimize gaps in schedule
        if "no_gaps" in preferences:
            # Prefer consecutive lessons
            # This can be implemented through additional clauses that encourage
            # consecutive time slots
            pass  # Implementation depends on specific requirements

        # Teacher preferences
        if "teacher_preferences" in preferences:
            for lesson_id, teacher_id, class_id, room_id, time_slot_id in preferences[
                "teacher_preferences"
            ]:
                key = (lesson_id, teacher_id, class_id, room_id, time_slot_id)
                if key in self.variables:
                    # Add as desirable (can use weighted clauses)
                    var = self.variables[key]
                    # In simple case add as regular clause
                    self.cnf.append([var])

    def encode_custom_constraints(self, constraints: List[Dict]) -> None:
        """
        Encodes custom constraints from Constraint table.

        Args:
            constraints: List of constraints with fields constraint_type and constraint_data
        """
        for constraint in constraints:
            constraint_type = constraint.get("constraint_type")
            constraint_data = constraint.get("constraint_data", {})
            priority = constraint.get("priority", 1)

            if constraint_type == "teacher_unavailable":
                # Teacher unavailable at certain time
                teacher_id = constraint_data.get("teacher_id")
                unavailable_time_slots = constraint_data.get("time_slot_ids", [])
                for time_slot_id in unavailable_time_slots:
                    teacher_time_vars = [
                        var
                        for (
                            l_id,
                            t_id,
                            cg_id,
                            r_id,
                            ts_id,
                        ), var in self.variables.items()
                        if t_id == teacher_id and ts_id == time_slot_id
                    ]
                    # Forbid all combinations with this teacher and time slot
                    for var in teacher_time_vars:
                        self.cnf.append([-var])

            elif constraint_type == "room_unavailable":
                # Room unavailable at certain time
                room_id = constraint_data.get("room_id")
                unavailable_time_slots = constraint_data.get("time_slot_ids", [])
                for time_slot_id in unavailable_time_slots:
                    room_time_vars = [
                        var
                        for (
                            l_id,
                            t_id,
                            cg_id,
                            r_id,
                            ts_id,
                        ), var in self.variables.items()
                        if r_id == room_id and ts_id == time_slot_id
                    ]
                    # Forbid all combinations with this room and time slot
                    for var in room_time_vars:
                        self.cnf.append([-var])

            elif constraint_type == "class_preference":
                # Class preferences (e.g., no more than N lessons per day)
                class_group_id = constraint_data.get("class_group_id")
                max_daily_lessons = constraint_data.get("max_daily_lessons")
                if max_daily_lessons:
                    # For each day of week limit number of lessons
                    # This requires grouping by day of week
                    pass  # Simplified implementation
            
            elif constraint_type == "study_group_preference":
                # Study group preferences (similar to class preferences)
                study_group_id = constraint_data.get("study_group_id")
                max_daily_lessons = constraint_data.get("max_daily_lessons")
                if max_daily_lessons:
                    # For each day of week limit number of lessons
                    pass  # Simplified implementation

            elif constraint_type == "consecutive_preference":
                # Preference for consecutive lessons
                # Can add clauses encouraging sequence
                pass

    def get_cnf(self) -> CNF:
        """Returns CNF formula."""
        return self.cnf

    def get_variable_mapping(self) -> Dict[Tuple[UUID, int, UUID, UUID, UUID], int]:
        """Returns mapping of combinations to variables."""
        return self.variables.copy()

    def get_reverse_mapping(self) -> Dict[int, Tuple[UUID, int, UUID, UUID, UUID]]:
        """Returns reverse mapping of variables to combinations."""
        return self.reverse_variables.copy()
