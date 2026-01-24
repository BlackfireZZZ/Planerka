"""
Teacher model for storing teachers.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    full_name = Column(String, nullable=False)
    subject = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    institution = relationship("Institution", lazy="selectin")
    teacher_lessons = relationship(
        "TeacherLesson",
        back_populates="teacher",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    schedule_entries = relationship(
        "ScheduleEntry",
        back_populates="teacher",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
