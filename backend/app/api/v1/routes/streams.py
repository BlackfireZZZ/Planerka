"""API routes for managing streams."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.stream import StreamCreate, StreamResponse, StreamUpdate
from app.core.dependencies import get_current_user
from app.db.models.class_group import ClassGroup
from app.db.models.institution import Institution
from app.db.models.stream import Stream, stream_class_group
from app.db.models.user import User
from app.db.session import get_db_session

router = APIRouter(prefix="/streams", tags=["Streams"])


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


@router.post("", status_code=status.HTTP_201_CREATED, response_model=StreamResponse)
async def create_stream(
    data: StreamCreate,
    institution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> StreamResponse:
    """Create a new stream."""
    await verify_institution_access(institution_id, current_user, db)
    
    # Verify all class groups belong to the institution
    if data.class_group_ids:
        result = await db.execute(
            select(ClassGroup).where(
                ClassGroup.id.in_(data.class_group_ids),
                ClassGroup.institution_id == institution_id,
            )
        )
        class_groups = result.scalars().all()
        if len(class_groups) != len(data.class_group_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some class groups not found or don't belong to this institution",
            )
    
    stream = Stream(
        id=uuid4(),
        institution_id=institution_id,
        name=data.name,
    )
    db.add(stream)
    await db.flush()
    
    # Add class groups to stream
    if data.class_group_ids:
        for class_group_id in data.class_group_ids:
            await db.execute(
                stream_class_group.insert().values(
                    stream_id=stream.id, class_group_id=class_group_id
                )
            )
    
    await db.commit()
    await db.refresh(stream)
    
    # Load class groups for response
    result = await db.execute(
        select(ClassGroup)
        .join(stream_class_group)
        .where(stream_class_group.c.stream_id == stream.id)
    )
    class_groups = result.scalars().all()
    
    response = StreamResponse(
        id=stream.id,
        institution_id=stream.institution_id,
        name=stream.name,
        created_at=stream.created_at,
        updated_at=stream.updated_at,
        class_groups=[
            {"id": str(cg.id), "name": cg.name} for cg in class_groups
        ],
    )
    return response


@router.get("", response_model=list[StreamResponse])
async def list_streams(
    institution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[StreamResponse]:
    """Get list of streams."""
    await verify_institution_access(institution_id, current_user, db)
    result = await db.execute(
        select(Stream).where(Stream.institution_id == institution_id)
    )
    streams = result.scalars().all()
    
    responses = []
    for stream in streams:
        result = await db.execute(
            select(ClassGroup)
            .join(stream_class_group)
            .where(stream_class_group.c.stream_id == stream.id)
        )
        class_groups = result.scalars().all()
        response = StreamResponse(
            id=stream.id,
            institution_id=stream.institution_id,
            name=stream.name,
            created_at=stream.created_at,
            updated_at=stream.updated_at,
            class_groups=[
                {"id": str(cg.id), "name": cg.name} for cg in class_groups
            ],
        )
        responses.append(response)
    
    return responses


@router.get("/{stream_id}", response_model=StreamResponse)
async def get_stream(
    stream_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> StreamResponse:
    """Get stream by ID."""
    result = await db.execute(
        select(Stream)
        .join(Institution)
        .where(Stream.id == stream_id, Institution.user_id == current_user.id)
    )
    stream = result.scalar_one_or_none()
    if not stream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Stream not found"
        )
    
    # Load class groups
    result = await db.execute(
        select(ClassGroup)
        .join(stream_class_group)
        .where(stream_class_group.c.stream_id == stream.id)
    )
    class_groups = result.scalars().all()
    
    response = StreamResponse(
        id=stream.id,
        institution_id=stream.institution_id,
        name=stream.name,
        created_at=stream.created_at,
        updated_at=stream.updated_at,
        class_groups=[
            {"id": str(cg.id), "name": cg.name} for cg in class_groups
        ],
    )
    return response


@router.put("/{stream_id}", response_model=StreamResponse)
async def update_stream(
    stream_id: UUID,
    data: StreamUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> StreamResponse:
    """Update stream."""
    result = await db.execute(
        select(Stream)
        .join(Institution)
        .where(Stream.id == stream_id, Institution.user_id == current_user.id)
    )
    stream = result.scalar_one_or_none()
    if not stream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Stream not found"
        )
    
    if data.name is not None:
        stream.name = data.name
    
    # Update class groups if provided
    if data.class_group_ids is not None:
        # Verify all class groups belong to the institution
        if data.class_group_ids:
            result = await db.execute(
                select(ClassGroup).where(
                    ClassGroup.id.in_(data.class_group_ids),
                    ClassGroup.institution_id == stream.institution_id,
                )
            )
            class_groups = result.scalars().all()
            if len(class_groups) != len(data.class_group_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Some class groups not found or don't belong to this institution",
                )
        
        # Remove existing associations
        await db.execute(
            stream_class_group.delete().where(
                stream_class_group.c.stream_id == stream.id
            )
        )
        
        # Add new associations
        if data.class_group_ids:
            for class_group_id in data.class_group_ids:
                await db.execute(
                    stream_class_group.insert().values(
                        stream_id=stream.id, class_group_id=class_group_id
                    )
                )
    
    await db.commit()
    await db.refresh(stream)
    
    # Load class groups for response
    result = await db.execute(
        select(ClassGroup)
        .join(stream_class_group)
        .where(stream_class_group.c.stream_id == stream.id)
    )
    class_groups = result.scalars().all()
    
    response = StreamResponse(
        id=stream.id,
        institution_id=stream.institution_id,
        name=stream.name,
        created_at=stream.created_at,
        updated_at=stream.updated_at,
        class_groups=[
            {"id": str(cg.id), "name": cg.name} for cg in class_groups
        ],
    )
    return response


@router.delete("/{stream_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stream(
    stream_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete stream."""
    result = await db.execute(
        select(Stream)
        .join(Institution)
        .where(Stream.id == stream_id, Institution.user_id == current_user.id)
    )
    stream = result.scalar_one_or_none()
    if not stream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Stream not found"
        )
    await db.delete(stream)
    await db.commit()
