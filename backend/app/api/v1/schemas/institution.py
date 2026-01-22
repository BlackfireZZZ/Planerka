"""
Pydantic schemas for Institution.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class InstitutionCreate(BaseModel):
    """Schema for creating an institution."""

    name: str = Field(..., min_length=1, max_length=255)


class InstitutionUpdate(BaseModel):
    """Schema for updating an institution."""

    name: str | None = Field(None, min_length=1, max_length=255)


class InstitutionResponse(BaseModel):
    """Response schema for institution."""

    id: UUID
    name: str
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
