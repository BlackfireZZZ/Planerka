"""API routes for managing rooms."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.room import RoomCreate, RoomResponse, RoomUpdate
from app.core.dependencies import get_current_user
from app.db.models.institution import Institution
from app.db.models.room import Room
from app.db.models.user import User
from app.db.session import get_db_session

router = APIRouter(prefix="/rooms", tags=["Rooms"])


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


@router.post("", status_code=status.HTTP_201_CREATED, response_model=RoomResponse)
async def create_room(
    data: RoomCreate,
    institution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> RoomResponse:
    """Create a new room."""
    await verify_institution_access(institution_id, current_user, db)
    room = Room(
        id=uuid4(),
        institution_id=institution_id,
        name=data.name,
        capacity=data.capacity,
        room_type=data.room_type,
        equipment=data.equipment,
    )
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return RoomResponse.model_validate(room)


@router.get("", response_model=list[RoomResponse])
async def list_rooms(
    institution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[RoomResponse]:
    """Get list of rooms."""
    await verify_institution_access(institution_id, current_user, db)
    result = await db.execute(select(Room).where(Room.institution_id == institution_id))
    rooms = result.scalars().all()
    return [RoomResponse.model_validate(room) for room in rooms]


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> RoomResponse:
    """Get room by ID."""
    result = await db.execute(
        select(Room)
        .join(Institution)
        .where(Room.id == room_id, Institution.user_id == current_user.id)
    )
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Room not found"
        )
    return RoomResponse.model_validate(room)


@router.put("/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: UUID,
    data: RoomUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> RoomResponse:
    """Update room."""
    result = await db.execute(
        select(Room)
        .join(Institution)
        .where(Room.id == room_id, Institution.user_id == current_user.id)
    )
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Room not found"
        )
    if data.name is not None:
        room.name = data.name
    if data.capacity is not None:
        room.capacity = data.capacity
    if data.room_type is not None:
        room.room_type = data.room_type
    if data.equipment is not None:
        room.equipment = data.equipment
    await db.commit()
    await db.refresh(room)
    return RoomResponse.model_validate(room)


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    room_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete room."""
    result = await db.execute(
        select(Room)
        .join(Institution)
        .where(Room.id == room_id, Institution.user_id == current_user.id)
    )
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Room not found"
        )
    await db.delete(room)
    await db.commit()
