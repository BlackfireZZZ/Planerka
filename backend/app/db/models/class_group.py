"""
ClassGroup model for storing class groups.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class ClassGroup(Base):
    __tablename__ = "class_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    institution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String, nullable=False)
    student_count = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    institution = relationship(
        "Institution", back_populates="class_groups", lazy="selectin"
    )
    students = relationship(
        "Student",
        back_populates="class_group",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    schedule_entries = relationship(
        "ScheduleEntry",
        back_populates="class_group",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    streams = relationship(
        "Stream",
        secondary="stream_class_groups",
        back_populates="class_groups",
        lazy="selectin",
    )