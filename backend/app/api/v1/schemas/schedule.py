"""
Pydantic schemas for Schedule.
"""

from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field


class ScheduleCreate(BaseModel):
    """Schema for creating a schedule."""

    name: str = Field(..., min_length=1, max_length=255)
    academic_period: str | None = Field(None, max_length=100)


class ScheduleUpdate(BaseModel):
    """Schema for updating a schedule."""

    name: str | None = Field(None, min_length=1, max_length=255)
    academic_period: str | None = Field(None, max_length=100)
    status: str | None = Field(None, pattern="^(draft|generated|active)$")


class ScheduleGenerateRequest(BaseModel):
    """Schema for schedule generation request."""

    timeout: int = Field(300, ge=10, le=3600, description="Timeout in seconds")


class ScheduleEntryResponse(BaseModel):
    """Response schema for schedule entry."""

    id: UUID
    institution_id: UUID
    schedule_id: UUID
    lesson_id: UUID
    teacher_id: int
    class_group_id: UUID | None
    study_group_id: UUID | None
    room_id: UUID
    time_slot_id: UUID
    week_number: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScheduleResponse(BaseModel):
    """Response schema for schedule."""

    id: UUID
    institution_id: UUID
    name: str
    academic_period: str | None
    status: str
    generated_at: datetime | None
    created_at: datetime
    updated_at: datetime
    entries: List[ScheduleEntryResponse] = []

    class Config:
        from_attributes = True


class ScheduleGenerateResponse(BaseModel):
    """Response schema for schedule generation."""

    success: bool
    message: str
    entries_count: int | None = None
