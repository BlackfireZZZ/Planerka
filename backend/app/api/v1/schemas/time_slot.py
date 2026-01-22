"""
Pydantic schemas for TimeSlot.
"""

from datetime import datetime, time
from uuid import UUID

from pydantic import BaseModel, Field


class TimeSlotCreate(BaseModel):
    """Schema for creating a time slot."""

    day_of_week: int = Field(..., ge=0, le=6)  # 0 = Monday, 6 = Sunday
    start_time: time
    end_time: time
    slot_number: int = Field(..., ge=0)


class TimeSlotUpdate(BaseModel):
    """Schema for updating a time slot."""

    day_of_week: int | None = Field(None, ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None
    slot_number: int | None = Field(None, ge=0)


class TimeSlotResponse(BaseModel):
    """Response schema for time slot."""

    id: UUID
    institution_id: UUID
    day_of_week: int
    start_time: time
    end_time: time
    slot_number: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
