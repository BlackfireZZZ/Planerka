"""
Lesson model for storing subjects/lessons.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    institution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String, nullable=False)
    subject_code = Column(String, nullable=True)
    duration_minutes = Column(Integer, nullable=False, default=90)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    institution = relationship("Institution", back_populates="lessons", lazy="selectin")
    teacher_lessons = relationship(
        "TeacherLesson",
        back_populates="lesson",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    schedule_entries = relationship(
        "ScheduleEntry",
        back_populates="lesson",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    class_groups = relationship(
        "ClassGroup",
        secondary="class_group_lessons",
        back_populates="lessons",
        lazy="selectin",
    )
    study_groups = relationship(
        "StudyGroup",
        secondary="study_group_lessons",
        back_populates="lessons",
        lazy="selectin",
    )
