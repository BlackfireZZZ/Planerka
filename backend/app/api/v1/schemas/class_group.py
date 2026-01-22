"""
Pydantic schemas for ClassGroup.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ClassGroupCreate(BaseModel):
    """Schema for creating a class group."""

    name: str = Field(..., min_length=1, max_length=255)
    student_count: int = Field(0, ge=0)


class ClassGroupUpdate(BaseModel):
    """Schema for updating a class group."""

    name: str | None = Field(None, min_length=1, max_length=255)
    student_count: int | None = Field(None, ge=0)


class ClassGroupResponse(BaseModel):
    """Response schema for class group."""

    id: UUID
    institution_id: UUID
    name: str
    student_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
