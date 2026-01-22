"""
Pydantic schemas for Teacher.
"""

from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field


class TeacherCreate(BaseModel):
    """Schema for creating a teacher."""

    full_name: str = Field(..., min_length=1, max_length=255)
    subject: str | None = Field(None, max_length=255)


class TeacherUpdate(BaseModel):
    """Schema for updating a teacher."""

    full_name: str | None = Field(None, min_length=1, max_length=255)
    subject: str | None = Field(None, max_length=255)


class TeacherResponse(BaseModel):
    """Response schema for teacher."""

    id: int
    institution_id: UUID
    full_name: str
    subject: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TeacherLessonAssign(BaseModel):
    """Schema for assigning lessons to a teacher."""

    lesson_ids: List[UUID] = Field(..., min_length=1)


class TeacherLessonResponse(BaseModel):
    """Response schema for teacher-lesson association."""

    id: UUID
    teacher_id: int
    lesson_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
