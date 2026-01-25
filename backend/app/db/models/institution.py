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
    user = relationship("User", back_populates="institutions", lazy="noload")
    class_groups = relationship(
        "ClassGroup",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    students = relationship(
        "Student",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    lessons = relationship(
        "Lesson",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    rooms = relationship(
        "Room",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    time_slots = relationship(
        "TimeSlot",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    constraints = relationship(
        "Constraint",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    schedules = relationship(
        "Schedule",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    streams = relationship(
        "Stream",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    study_groups = relationship(
        "StudyGroup",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="noload",
    )
