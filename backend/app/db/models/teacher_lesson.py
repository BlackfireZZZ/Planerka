"""
TeacherLesson model for many-to-many relationship between Teacher and Lesson.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class TeacherLesson(Base):
    __tablename__ = "teacher_lessons"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    teacher_id = Column(
        Integer,
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lesson_id = Column(
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    teacher = relationship("Teacher", back_populates="teacher_lessons", lazy="selectin")
    lesson = relationship("Lesson", back_populates="teacher_lessons", lazy="selectin")
