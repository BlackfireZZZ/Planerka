"""
Pydantic schemas for StudyGroup.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class StudyGroupCreate(BaseModel):
    """Schema for creating a study group."""

    stream_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    student_ids: list[UUID] = Field(default_factory=list)


class StudyGroupUpdate(BaseModel):
    """Schema for updating a study group."""

    stream_id: UUID | None = None
    name: str | None = Field(None, min_length=1, max_length=255)
    student_ids: list[UUID] | None = None


class StudyGroupResponse(BaseModel):
    """Response schema for study group."""

    id: UUID
    institution_id: UUID
    stream_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    students: list[dict] = Field(default_factory=list)

    class Config:
        from_attributes = True


class StudyGroupLessonAssign(BaseModel):
    """Schema for assigning lessons to a study group."""

    lesson_ids: list[UUID] = Field(default_factory=list, min_length=0)


class StudyGroupLessonLink(BaseModel):
    """Response schema for study group-lesson association."""

    lesson_id: UUID
