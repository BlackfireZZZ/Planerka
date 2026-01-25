"""
Tests for schedule generation, especially parallel lessons in the same time slot.

Different classes (or study groups with no overlapping students) CAN run in the same
time slot when they use different teachers and different rooms.
"""

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scheduler.schedule_generator import ScheduleGenerator


def _run(coro):
    """Run async test without pytest-asyncio."""
    return asyncio.run(coro)


@pytest.mark.parametrize("use_class_groups", [True, False])
def test_two_groups_same_slot_no_conflict(use_class_groups):
    """
    Two different groups (class groups or study groups with no overlapping students),
    one time slot, two teachers, two rooms. Both (lesson, group) pairs must be
    scheduled in the same slot; this is valid because there is no resource conflict.
    """
    lu1, lu2 = uuid.uuid4(), uuid.uuid4()
    g1, g2 = uuid.uuid4(), uuid.uuid4()
    r1, r2 = uuid.uuid4(), uuid.uuid4()
    ts1 = uuid.uuid4()

    if use_class_groups:
        class_groups = [g1, g2]
        study_groups = []
        class_group_lessons = {g1: {lu1: 1}, g2: {lu2: 1}}
        study_group_lessons = {}
    else:
        class_groups = []
        study_groups = [g1, g2]
        class_group_lessons = {}
        study_group_lessons = {g1: {lu1: 1}, g2: {lu2: 1}}

    data = {
        "lessons": [lu1, lu2],
        "teachers": [1, 2],
        "class_groups": class_groups,
        "study_groups": study_groups,
        "rooms": [r1, r2],
        "time_slots": [ts1],
        "teacher_lessons": {1: {lu1}, 2: {lu2}},
        "class_group_lessons": class_group_lessons,
        "study_group_lessons": study_group_lessons,
        "room_capacities": {r1: 30, r2: 30},
        "class_group_sizes": {g1: 10, g2: 10} if use_class_groups else {},
        "study_group_sizes": {g1: 10, g2: 10} if not use_class_groups else {},
        "student_group_memberships": {},  # no overlap: class groups are disjoint; study groups have no shared students
        "constraints": [],
    }

    async def run_generate():
        db = MagicMock()
        gen = ScheduleGenerator(db)
        with patch.object(
            gen.constraint_builder,
            "build_from_institution",
            new_callable=AsyncMock,
            return_value=data,
        ):
            return await gen.generate(uuid.uuid4(), timeout=15)

    ok, entries, err = _run(run_generate())
    assert ok is True, f"expected success, got err={err}"
    assert entries is not None
    assert len(entries) == 2
    slots = {e["time_slot_id"] for e in entries}
    assert len(slots) == 1
    assert ts1 in slots


def test_unsat_returns_diagnostic():
    """
    When no solution exists (e.g. two pairs must use the same teacher and same room
    in the only slot), the generator returns a specific diagnostic instead of
    a generic "Constraints may be too restrictive".
    """
    lu1, lu2 = uuid.uuid4(), uuid.uuid4()
    cg1, cg2 = uuid.uuid4(), uuid.uuid4()
    r1 = uuid.uuid4()  # only one room
    ts1 = uuid.uuid4()  # only one slot
    # One teacher for both lessons -> teacher conflict in the same slot
    data = {
        "lessons": [lu1, lu2],
        "teachers": [1],
        "class_groups": [cg1, cg2],
        "study_groups": [],
        "rooms": [r1],
        "time_slots": [ts1],
        "teacher_lessons": {1: {lu1, lu2}},
        "class_group_lessons": {cg1: {lu1: 1}, cg2: {lu2: 1}},
        "study_group_lessons": {},
        "room_capacities": {r1: 30},
        "class_group_sizes": {cg1: 10, cg2: 10},
        "study_group_sizes": {},
        "student_group_memberships": {},
        "constraints": [],
    }

    async def run_generate():
        db = MagicMock()
        gen = ScheduleGenerator(db)
        with patch.object(
            gen.constraint_builder,
            "build_from_institution",
            new_callable=AsyncMock,
            return_value=data,
        ):
            return await gen.generate(uuid.uuid4(), timeout=10)

    ok, entries, err = _run(run_generate())
    assert ok is False
    assert entries is None
    assert err is not None
    # Should mention resource conflict (teacher/room/student), not a generic message
    assert "resource" in err.lower() or "conflict" in err.lower()
    assert "Constraints may be too restrictive" not in (err or "")


def test_count_two_slots_for_one_lesson_group():
    """
    One class group, one lesson type with count=2. Need 2 time slots (or 2 rooms, 2 teachers)
    so the scheduler places exactly 2 entries for that (lesson, group).
    """
    lu1 = uuid.uuid4()
    cg1 = uuid.uuid4()
    r1, r2 = uuid.uuid4(), uuid.uuid4()
    ts1, ts2 = uuid.uuid4(), uuid.uuid4()
    data = {
        "lessons": [lu1],
        "teachers": [1],
        "class_groups": [cg1],
        "study_groups": [],
        "rooms": [r1, r2],
        "time_slots": [ts1, ts2],
        "teacher_lessons": {1: {lu1}},
        "class_group_lessons": {cg1: {lu1: 2}},
        "study_group_lessons": {},
        "room_capacities": {r1: 30, r2: 30},
        "class_group_sizes": {cg1: 10},
        "study_group_sizes": {},
        "student_group_memberships": {},
        "constraints": [],
    }

    async def run_generate():
        db = MagicMock()
        gen = ScheduleGenerator(db)
        with patch.object(
            gen.constraint_builder,
            "build_from_institution",
            new_callable=AsyncMock,
            return_value=data,
        ):
            return await gen.generate(uuid.uuid4(), timeout=15)

    ok, entries, err = _run(run_generate())
    assert ok is True, f"expected success, got err={err}"
    assert entries is not None
    assert len(entries) == 2
    for e in entries:
        assert e["lesson_id"] == lu1
        assert e["class_group_id"] == cg1
        assert e["study_group_id"] is None
    time_slots_used = {e["time_slot_id"] for e in entries}
    assert len(time_slots_used) == 2
    assert ts1 in time_slots_used
    assert ts2 in time_slots_used
