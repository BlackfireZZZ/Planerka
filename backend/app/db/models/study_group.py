"""
StudyGroup model for storing study groups (flexible groups of students from different class groups).
"""

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, func
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
study_group_student = Table(
    "study_group_students",
    Base.metadata,
    Column(
        "study_group_id",
        UUID(as_uuid=True),
        ForeignKey("study_groups.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "student_id",
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class StudyGroup(Base):
    __tablename__ = "study_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    institution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stream_id = Column(
        UUID(as_uuid=True),
        ForeignKey("streams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    institution = relationship(
        "Institution", back_populates="study_groups", lazy="selectin"
    )
    stream = relationship("Stream", back_populates="study_groups", lazy="selectin")
    students = relationship(
        "Student",
        secondary=study_group_student,
        back_populates="study_groups",
        lazy="selectin",
    )
    schedule_entries = relationship(
        "ScheduleEntry",
        back_populates="study_group",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
