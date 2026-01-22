"""
Pydantic schemas for Constraint.
"""

from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from pydantic import BaseModel, Field


class ConstraintCreate(BaseModel):
    """Schema for creating a constraint."""

    constraint_type: str = Field(
        ...,
        description="Type of constraint: teacher_unavailable, room_unavailable, class_preference, etc.",
    )
    constraint_data: Dict[str, Any] = Field(
        ..., description="Constraint data in JSON format"
    )
    priority: int = Field(
        1, ge=0, le=1, description="1 = hard constraint, 0 = soft constraint"
    )


class ConstraintUpdate(BaseModel):
    """Schema for updating a constraint."""

    constraint_type: str | None = None
    constraint_data: Dict[str, Any] | None = None
    priority: int | None = Field(None, ge=0, le=1)


class ConstraintResponse(BaseModel):
    """Response schema for constraint."""

    id: UUID
    institution_id: UUID
    constraint_type: str
    constraint_data: Dict[str, Any]
    priority: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
