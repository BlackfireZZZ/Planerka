"""
Stream model for storing streams (collections of class groups).
"""

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, func
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base

stream_class_group = Table(
    "stream_class_groups",
    Base.metadata,
    Column(
        "stream_id",
        UUID(as_uuid=True),
        ForeignKey("streams.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "class_group_id",
        UUID(as_uuid=True),
        ForeignKey("class_groups.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Stream(Base):
    __tablename__ = "streams"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    institution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    institution = relationship("Institution", back_populates="streams", lazy="selectin")
    class_groups = relationship(
        "ClassGroup",
        secondary=stream_class_group,
        back_populates="streams",
        lazy="selectin",
    )
    study_groups = relationship(
        "StudyGroup",
        back_populates="stream",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
