"""
Student model for storing students.
"""

from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    institution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    class_group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("class_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    full_name = Column(String, nullable=False)
    student_number = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    institution = relationship(
        "Institution", back_populates="students", lazy="selectin"
    )
    class_group = relationship("ClassGroup", back_populates="students", lazy="selectin")
    study_groups = relationship(
        "StudyGroup",
        secondary="study_group_students",
        back_populates="students",
        lazy="selectin",
    )
