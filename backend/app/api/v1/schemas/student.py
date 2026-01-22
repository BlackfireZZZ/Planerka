"""
Pydantic schemas for Student.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class StudentCreate(BaseModel):
    """Schema for creating a student."""

    class_group_id: UUID
    full_name: str = Field(..., min_length=1, max_length=255)
    student_number: str | None = Field(None, max_length=50)


class StudentUpdate(BaseModel):
    """Schema for updating a student."""

    class_group_id: UUID | None = None
    full_name: str | None = Field(None, min_length=1, max_length=255)
    student_number: str | None = Field(None, max_length=50)


class StudentResponse(BaseModel):
    """Response schema for student."""

    id: UUID
    institution_id: UUID
    class_group_id: UUID
    full_name: str
    student_number: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
