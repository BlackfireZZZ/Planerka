"""
Pydantic schemas for Stream.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class StreamCreate(BaseModel):
    """Schema for creating a stream."""

    name: str = Field(..., min_length=1, max_length=255)
    class_group_ids: list[UUID] = Field(default_factory=list)


class StreamUpdate(BaseModel):
    """Schema for updating a stream."""

    name: str | None = Field(None, min_length=1, max_length=255)
    class_group_ids: list[UUID] | None = None


class StreamResponse(BaseModel):
    """Response schema for stream."""

    id: UUID
    institution_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    class_groups: list[dict] = Field(default_factory=list)

    class Config:
        from_attributes = True
