"""
Institution model for storing educational institutions.
"""

from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    name = Column(String, nullable=False)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="institutions", lazy="selectin")
    class_groups = relationship(
        "ClassGroup",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    students = relationship(
        "Student",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    lessons = relationship(
        "Lesson",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    rooms = relationship(
        "Room",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    time_slots = relationship(
        "TimeSlot",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    constraints = relationship(
        "Constraint",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    schedules = relationship(
        "Schedule",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    streams = relationship(
        "Stream",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    study_groups = relationship(
        "StudyGroup",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="selectin",
    )