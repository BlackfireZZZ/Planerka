"""
TimeSlot model for storing time slots.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Time, func
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class TimeSlot(Base):
    __tablename__ = "time_slots"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    institution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day_of_week = Column(Integer, nullable=False)  # 0 = Monday, 6 = Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_number = Column(Integer, nullable=False)  # Order within the day

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    institution = relationship(
        "Institution", back_populates="time_slots", lazy="selectin"
    )
    schedule_entries = relationship(
        "ScheduleEntry",
        back_populates="time_slot",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
