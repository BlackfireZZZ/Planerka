"""
Module for solving SAT problem and extracting schedule.
"""

from typing import Dict, List, Optional, Tuple
from uuid import UUID

from pysat.solvers import Solver

from app.scheduler.sat_encoder import ScheduleEncoder


class ScheduleSolver:
    """
    Class for solving SAT problem and extracting schedule from solution.
    """

    def __init__(self, encoder: ScheduleEncoder):
        self.encoder = encoder
        self.solver: Optional[Solver] = None

    def solve(self, timeout: int = 300) -> bool:
        """
        Solves SAT problem.

        Args:
            timeout: Maximum solving time in seconds

        Returns:
            True if solution found, False otherwise
        """
        cnf = self.encoder.get_cnf()
        self.solver = Solver(name="glucose3", bootstrap_with=cnf)
        try:
            self.solver.set_timeout(timeout)
        except AttributeError:
            pass

        return self.solver.solve()

    def extract_schedule(self) -> List[Tuple[UUID, int, UUID, UUID, UUID]]:
        """
        Extracts schedule from SAT problem solution.

        Returns:
            List of tuples (lesson_id, teacher_id, group_id, room_id, time_slot_id)
            where group_id can be either class_group_id or study_group_id
        """
        if not self.solver:
            raise ValueError("Solver not initialized. Call solve() first.")

        model = self.solver.get_model()
        if not model:
            return []

        reverse_mapping = self.encoder.get_reverse_mapping()
        schedule = []

        for var in model:
            if var > 0 and var in reverse_mapping:
                schedule.append(reverse_mapping[var])

        return schedule

    def optimize(self) -> List[Tuple[UUID, int, UUID, UUID, UUID]]:
        """
        Optimizes schedule considering soft constraints.

        In current implementation simply returns first found solution.
        For more complex optimization can use MAX-SAT solver.

        Returns:
            Optimized schedule
        """
        if self.solve():
            return self.extract_schedule()
        return []

    def close(self) -> None:
        """Closes solver and releases resources."""
        if self.solver:
            self.solver.delete()
            self.solver = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
