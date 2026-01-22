"""API routes for managing time slots."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.time_slot import (
    TimeSlotCreate,
    TimeSlotResponse,
    TimeSlotUpdate,
)
from app.core.dependencies import get_current_user
from app.db.models.institution import Institution
from app.db.models.time_slot import TimeSlot
from app.db.models.user import User
from app.db.session import get_db_session

router = APIRouter(prefix="/time-slots", tags=["Time Slots"])


async def verify_institution_access(
    institution_id: UUID, current_user: User, db: AsyncSession
) -> Institution:
    """Verifies access to the institution."""
    result = await db.execute(
        select(Institution).where(
            Institution.id == institution_id, Institution.user_id == current_user.id
        )
    )
    institution = result.scalar_one_or_none()
    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found"
        )
    return institution


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TimeSlotResponse)
async def create_time_slot(
    data: TimeSlotCreate,
    institution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> TimeSlotResponse:
    """Create a new time slot."""
    await verify_institution_access(institution_id, current_user, db)
    time_slot = TimeSlot(
        id=uuid4(),
        institution_id=institution_id,
        day_of_week=data.day_of_week,
        start_time=data.start_time,
        end_time=data.end_time,
        slot_number=data.slot_number,
    )
    db.add(time_slot)
    await db.commit()
    await db.refresh(time_slot)
    return TimeSlotResponse.model_validate(time_slot)


@router.get("", response_model=list[TimeSlotResponse])
async def list_time_slots(
    institution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[TimeSlotResponse]:
    """Get list of time slots."""
    await verify_institution_access(institution_id, current_user, db)
    result = await db.execute(
        select(TimeSlot).where(TimeSlot.institution_id == institution_id)
    )
    time_slots = result.scalars().all()
    return [TimeSlotResponse.model_validate(ts) for ts in time_slots]


@router.get("/{time_slot_id}", response_model=TimeSlotResponse)
async def get_time_slot(
    time_slot_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> TimeSlotResponse:
    """Get time slot by ID."""
    result = await db.execute(
        select(TimeSlot)
        .join(Institution)
        .where(TimeSlot.id == time_slot_id, Institution.user_id == current_user.id)
    )
    time_slot = result.scalar_one_or_none()
    if not time_slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Time slot not found"
        )
    return TimeSlotResponse.model_validate(time_slot)


@router.put("/{time_slot_id}", response_model=TimeSlotResponse)
async def update_time_slot(
    time_slot_id: UUID,
    data: TimeSlotUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> TimeSlotResponse:
    """Update time slot."""
    result = await db.execute(
        select(TimeSlot)
        .join(Institution)
        .where(TimeSlot.id == time_slot_id, Institution.user_id == current_user.id)
    )
    time_slot = result.scalar_one_or_none()
    if not time_slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Time slot not found"
        )
    if data.day_of_week is not None:
        time_slot.day_of_week = data.day_of_week
    if data.start_time is not None:
        time_slot.start_time = data.start_time
    if data.end_time is not None:
        time_slot.end_time = data.end_time
    if data.slot_number is not None:
        time_slot.slot_number = data.slot_number
    await db.commit()
    await db.refresh(time_slot)
    return TimeSlotResponse.model_validate(time_slot)


@router.delete("/{time_slot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_time_slot(
    time_slot_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete time slot."""
    result = await db.execute(
        select(TimeSlot)
        .join(Institution)
        .where(TimeSlot.id == time_slot_id, Institution.user_id == current_user.id)
    )
    time_slot = result.scalar_one_or_none()
    if not time_slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Time slot not found"
        )
    await db.delete(time_slot)
    await db.commit()
