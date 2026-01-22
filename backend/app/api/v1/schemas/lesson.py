"""
Pydantic schemas for Lesson.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LessonCreate(BaseModel):
    """Schema for creating a lesson."""

    name: str = Field(..., min_length=1, max_length=255)
    subject_code: str | None = Field(None, max_length=50)
    duration_minutes: int = Field(90, ge=1, le=480)


class LessonUpdate(BaseModel):
    """Schema for updating a lesson."""

    name: str | None = Field(None, min_length=1, max_length=255)
    subject_code: str | None = Field(None, max_length=50)
    duration_minutes: int | None = Field(None, ge=1, le=480)


class LessonResponse(BaseModel):
    """Response schema for lesson."""

    id: UUID
    institution_id: UUID
    name: str
    subject_code: str | None
    duration_minutes: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
