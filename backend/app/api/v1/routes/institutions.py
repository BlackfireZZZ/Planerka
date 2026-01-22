"""
API routes for managing institutions.
"""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.institution import (
    InstitutionCreate,
    InstitutionResponse,
    InstitutionUpdate,
)
from app.core.dependencies import get_current_user
from app.db.models.institution import Institution
from app.db.models.user import User
from app.db.session import get_db_session

router = APIRouter(prefix="/institutions", tags=["Institutions"])


@router.post(
    "", status_code=status.HTTP_201_CREATED, response_model=InstitutionResponse
)
async def create_institution(
    data: InstitutionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> InstitutionResponse:
    """Create a new institution."""
    institution = Institution(
        id=uuid4(),
        name=data.name,
        user_id=current_user.id,
    )
    db.add(institution)
    await db.commit()
    await db.refresh(institution)
    return InstitutionResponse.model_validate(institution)


@router.get("", response_model=list[InstitutionResponse])
async def list_institutions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[InstitutionResponse]:
    """Get list of user's institutions."""
    result = await db.execute(
        select(Institution).where(Institution.user_id == current_user.id)
    )
    institutions = result.scalars().all()
    return [InstitutionResponse.model_validate(inst) for inst in institutions]


@router.get("/{institution_id}", response_model=InstitutionResponse)
async def get_institution(
    institution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> InstitutionResponse:
    """Get institution by ID."""
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
    return InstitutionResponse.model_validate(institution)


@router.put("/{institution_id}", response_model=InstitutionResponse)
async def update_institution(
    institution_id: UUID,
    data: InstitutionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> InstitutionResponse:
    """Update institution."""
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

    if data.name is not None:
        institution.name = data.name

    await db.commit()
    await db.refresh(institution)
    return InstitutionResponse.model_validate(institution)


@router.delete("/{institution_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_institution(
    institution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete institution."""
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

    await db.delete(institution)
    await db.commit()
