"""
Module for converting schedule constraints to CNF formula.
"""

from typing import Dict, List, Set, Tuple
from uuid import UUID

from pysat.card import CardEnc, EncType
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
        self.group_types: Dict[UUID, str] = {}
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
        class_group_lessons: Dict[UUID, Dict[UUID, int]],
        study_group_lessons: Dict[UUID, Dict[UUID, int]],
    ) -> None:
        """
        Creates boolean variables for all possible combinations.

        Only creates variables for (lesson, group) pairs that exist in
        class_group_lessons or study_group_lessons.
        """
        for cg_id in class_groups:
            self.group_types[cg_id] = "class_group"
        for sg_id in study_groups:
            self.group_types[sg_id] = "study_group"

        all_groups = class_groups + study_groups

        for lesson_id in lessons:
            for teacher_id in teachers:
                if lesson_id not in teacher_lessons.get(teacher_id, set()):
                    continue

                for group_id in all_groups:
                    group_type = self.group_types.get(group_id, "class_group")
                    if group_type == "class_group":
                        if lesson_id not in class_group_lessons.get(group_id, {}):
                            continue
                    else:
                        if lesson_id not in study_group_lessons.get(group_id, {}):
                            continue

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

    def get_infeasible_pairs(
        self,
        class_group_lessons: Dict[UUID, Dict[UUID, int]],
        study_group_lessons: Dict[UUID, Dict[UUID, int]],
        room_capacities: Dict[UUID, int],
        class_group_sizes: Dict[UUID, int],
        study_group_sizes: Dict[UUID, int],
    ) -> List[Tuple[UUID, UUID, str]]:
        """
        Returns (lesson_id, group_id, reason) for (lesson, group) pairs that have
        no valid variable (no teacher), only variables with insufficient room capacity,
        or fewer valid (teacher, room, time slot) combinations than the required count.
        """
        result: List[Tuple[UUID, UUID, str]] = []
        for cg_id, lessons_dict in class_group_lessons.items():
            for lesson_id, count in lessons_dict.items():
                vars_for = [
                    (var, key)
                    for key, var in self.variables.items()
                    if key[0] == lesson_id and key[2] == cg_id
                ]
                if not vars_for:
                    result.append(
                        (
                            lesson_id,
                            cg_id,
                            "no teacher is assigned to teach this lesson for this group",
                        )
                    )
                    continue
                if len(vars_for) < count:
                    result.append(
                        (
                            lesson_id,
                            cg_id,
                            "need {} lesson placements but only {} valid (teacher, room, time slot) combination(s) — add more time slots or resources".format(
                                count, len(vars_for)
                            ),
                        )
                    )
                    continue
                cap = class_group_sizes.get(cg_id, 0)
                if any(room_capacities.get(key[3], 0) >= cap for _, key in vars_for):
                    continue
                result.append(
                    (lesson_id, cg_id, "no room has sufficient capacity for this group")
                )
        for sg_id, lessons_dict in study_group_lessons.items():
            for lesson_id, count in lessons_dict.items():
                vars_for = [
                    (var, key)
                    for key, var in self.variables.items()
                    if key[0] == lesson_id and key[2] == sg_id
                ]
                if not vars_for:
                    result.append(
                        (
                            lesson_id,
                            sg_id,
                            "no teacher is assigned to teach this lesson for this group",
                        )
                    )
                    continue
                if len(vars_for) < count:
                    result.append(
                        (
                            lesson_id,
                            sg_id,
                            "need {} lesson placements but only {} valid (teacher, room, time slot) combination(s) — add more time slots or resources".format(
                                count, len(vars_for)
                            ),
                        )
                    )
                    continue
                cap = study_group_sizes.get(sg_id, 0)
                if any(room_capacities.get(key[3], 0) >= cap for _, key in vars_for):
                    continue
                result.append(
                    (lesson_id, sg_id, "no room has sufficient capacity for this group")
                )
        return result

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
        class_group_lessons: Dict[UUID, Dict[UUID, int]],
        study_group_lessons: Dict[UUID, Dict[UUID, int]],
        *,
        skip_conflicts: bool = False,
    ) -> None:
        """
        Encodes mandatory constraints (hard constraints).

        Hard constraints:
        1. Each (lesson_id, group_id) pair must be assigned exactly N times (N=count)
        2. Teacher cannot be in two places at the same time (conflict: teacher overlap)
        3. Same class/group cannot have two lessons at the same time (per group_id)
        4. Room cannot be occupied by two lessons simultaneously (conflict: room)
        5. Student set must not overlap: class vs study, study vs study (conflict: students)
        6. Room must have sufficient capacity

        If skip_conflicts=True, only (1) and (6) are applied (for diagnostic use).
        """
        for cg_id in class_groups:
            for lesson_id, count in class_group_lessons.get(cg_id, {}).items():
                lesson_vars = [
                    var
                    for (l_id, t_id, g_id, r_id, ts_id), var in self.variables.items()
                    if l_id == lesson_id and g_id == cg_id
                ]
                if len(lesson_vars) < count:
                    continue
                card_cnf = CardEnc.equals(
                    lits=lesson_vars,
                    bound=count,
                    top_id=self.next_var - 1,
                    encoding=EncType.seqcounter,
                )
                for cl in card_cnf.clauses:
                    self.cnf.append(cl)
                self.next_var = max(self.next_var, card_cnf.nv + 1)
        for sg_id in study_groups:
            for lesson_id, count in study_group_lessons.get(sg_id, {}).items():
                lesson_vars = [
                    var
                    for (l_id, t_id, g_id, r_id, ts_id), var in self.variables.items()
                    if l_id == lesson_id and g_id == sg_id
                ]
                if len(lesson_vars) < count:
                    continue
                card_cnf = CardEnc.equals(
                    lits=lesson_vars,
                    bound=count,
                    top_id=self.next_var - 1,
                    encoding=EncType.seqcounter,
                )
                for cl in card_cnf.clauses:
                    self.cnf.append(cl)
                self.next_var = max(self.next_var, card_cnf.nv + 1)

        if not skip_conflicts:
            # Conflict: teacher cannot be in two places at the same time
            for teacher_id in teachers:
                for time_slot_id in time_slots:
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
                    for i in range(len(teacher_time_vars)):
                        for j in range(i + 1, len(teacher_time_vars)):
                            self.cnf.append(
                                [-teacher_time_vars[i], -teacher_time_vars[j]]
                            )
            # Conflict: same class/group cannot have two lessons at the same time (per group_id)
            all_groups = class_groups + study_groups
            for group_id in all_groups:
                for time_slot_id in time_slots:
                    group_time_vars = [
                        var
                        for (
                            l_id,
                            t_id,
                            g_id,
                            r_id,
                            ts_id,
                        ), var in self.variables.items()
                        if g_id == group_id and ts_id == time_slot_id
                    ]
                    for i in range(len(group_time_vars)):
                        for j in range(i + 1, len(group_time_vars)):
                            self.cnf.append([-group_time_vars[i], -group_time_vars[j]])
            # Conflict: student set must not overlap (class vs study for same student)
            for student_id, memberships in student_group_memberships.items():
                class_group_id = memberships.get("class_group_id")
                study_group_ids = memberships.get("study_group_ids", [])
                if class_group_id and study_group_ids:
                    for study_group_id in study_group_ids:
                        for time_slot_id in time_slots:
                            class_vars = [
                                var
                                for (
                                    l_id,
                                    t_id,
                                    g_id,
                                    r_id,
                                    ts_id,
                                ), var in self.variables.items()
                                if g_id == class_group_id and ts_id == time_slot_id
                            ]
                            study_vars = [
                                var
                                for (
                                    l_id,
                                    t_id,
                                    g_id,
                                    r_id,
                                    ts_id,
                                ), var in self.variables.items()
                                if g_id == study_group_id and ts_id == time_slot_id
                            ]
                            for class_var in class_vars:
                                for study_var in study_vars:
                                    self.cnf.append([-class_var, -study_var])
            # Conflict: two study groups with overlapping students cannot run in the same slot
            overlapping_sg_pairs: Set[Tuple[UUID, UUID]] = set()
            for memberships in student_group_memberships.values():
                sgs = memberships.get("study_group_ids", [])
                for i in range(len(sgs)):
                    for j in range(i + 1, len(sgs)):
                        a, b = sgs[i], sgs[j]
                        if a != b:
                            overlapping_sg_pairs.add((min(a, b), max(a, b)))
            for sg_a, sg_b in overlapping_sg_pairs:
                for time_slot_id in time_slots:
                    a_vars = [
                        var
                        for (
                            l_id,
                            t_id,
                            g_id,
                            r_id,
                            ts_id,
                        ), var in self.variables.items()
                        if g_id == sg_a and ts_id == time_slot_id
                    ]
                    b_vars = [
                        var
                        for (
                            l_id,
                            t_id,
                            g_id,
                            r_id,
                            ts_id,
                        ), var in self.variables.items()
                        if g_id == sg_b and ts_id == time_slot_id
                    ]
                    for av in a_vars:
                        for bv in b_vars:
                            self.cnf.append([-av, -bv])
            # Conflict: room cannot be used by two lessons at the same time
            for room_id in rooms:
                for time_slot_id in time_slots:
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
                    for i in range(len(room_time_vars)):
                        for j in range(i + 1, len(room_time_vars)):
                            self.cnf.append([-room_time_vars[i], -room_time_vars[j]])
        for (l_id, t_id, g_id, r_id, ts_id), var in self.variables.items():
            room_capacity = room_capacities.get(r_id, 0)
            group_type = self.group_types.get(g_id, "class_group")
            if group_type == "class_group":
                group_size = class_group_sizes.get(g_id, 0)
            else:
                group_size = study_group_sizes.get(g_id, 0)
            if group_size > room_capacity:
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
        if "no_gaps" in preferences:
            pass
        if "teacher_preferences" in preferences:
            for lesson_id, teacher_id, class_id, room_id, time_slot_id in preferences[
                "teacher_preferences"
            ]:
                key = (lesson_id, teacher_id, class_id, room_id, time_slot_id)
                if key in self.variables:
                    var = self.variables[key]
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
                    for var in teacher_time_vars:
                        self.cnf.append([-var])

            elif constraint_type == "room_unavailable":
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
                    for var in room_time_vars:
                        self.cnf.append([-var])

            elif constraint_type == "class_preference":
                class_group_id = constraint_data.get("class_group_id")
                max_daily_lessons = constraint_data.get("max_daily_lessons")
                if max_daily_lessons:
                    pass

            elif constraint_type == "study_group_preference":
                study_group_id = constraint_data.get("study_group_id")
                max_daily_lessons = constraint_data.get("max_daily_lessons")
                if max_daily_lessons:
                    pass

            elif constraint_type == "consecutive_preference":
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
