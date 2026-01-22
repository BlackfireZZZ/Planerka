"""
Constraint model for storing schedule constraints.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Constraint(Base):
    __tablename__ = "constraints"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    institution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    constraint_type = Column(
        String, nullable=False
    )  # teacher_unavailable, room_unavailable, class_preference, etc.
    constraint_data = Column(
        JSON, nullable=False
    )  # Flexible JSON structure for different constraint types
    priority = Column(
        Integer, default=1, nullable=False
    )  # 1 = hard constraint, 0 = soft constraint

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    institution = relationship(
        "Institution", back_populates="constraints", lazy="selectin"
    )
