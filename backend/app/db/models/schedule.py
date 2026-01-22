"""
Schedule model for storing schedules.
"""

from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    institution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String, nullable=False)
    academic_period = Column(String, nullable=True)  # e.g., "Fall 2025", "Spring 2025"
    status = Column(String, default="draft", nullable=False)  # draft, generated, active
    generated_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    institution = relationship(
        "Institution", back_populates="schedules", lazy="selectin"
    )
    entries = relationship(
        "ScheduleEntry",
        back_populates="schedule",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
