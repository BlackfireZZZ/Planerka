"""
ScheduleEntry model for storing schedule entries.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class ScheduleEntry(Base):
    __tablename__ = "schedule_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    institution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    schedule_id = Column(
        UUID(as_uuid=True),
        ForeignKey("schedules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lesson_id = Column(
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    teacher_id = Column(
        Integer,
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    class_group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("class_groups.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    study_group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("study_groups.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    room_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    time_slot_id = Column(
        UUID(as_uuid=True),
        ForeignKey("time_slots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    week_number = Column(Integer, nullable=True)  # For multi-week schedules

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    institution = relationship("Institution", lazy="selectin")
    schedule = relationship("Schedule", back_populates="entries", lazy="selectin")
    lesson = relationship("Lesson", back_populates="schedule_entries", lazy="selectin")
    teacher = relationship(
        "Teacher", back_populates="schedule_entries", lazy="selectin"
    )
    class_group = relationship(
        "ClassGroup", back_populates="schedule_entries", lazy="selectin"
    )
    study_group = relationship(
        "StudyGroup", back_populates="schedule_entries", lazy="selectin"
    )
    room = relationship("Room", back_populates="schedule_entries", lazy="selectin")
    time_slot = relationship(
        "TimeSlot", back_populates="schedule_entries", lazy="selectin"
    )
