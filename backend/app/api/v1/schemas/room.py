"""
Pydantic schemas for Room.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RoomCreate(BaseModel):
    """Schema for creating a room."""

    name: str = Field(..., min_length=1, max_length=255)
    capacity: int = Field(..., ge=1)
    room_type: str | None = Field(None, max_length=50)
    equipment: str | None = None


class RoomUpdate(BaseModel):
    """Schema for updating a room."""

    name: str | None = Field(None, min_length=1, max_length=255)
    capacity: int | None = Field(None, ge=1)
    room_type: str | None = Field(None, max_length=50)
    equipment: str | None = None


class RoomResponse(BaseModel):
    """Response schema for room."""

    id: UUID
    institution_id: UUID
    name: str
    capacity: int
    room_type: str | None
    equipment: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
