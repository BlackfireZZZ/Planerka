"""API routes for managing constraints."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.constraint import (
    ConstraintCreate,
    ConstraintResponse,
    ConstraintUpdate,
)
from app.core.dependencies import get_current_user
from app.db.models.constraint import Constraint
from app.db.models.institution import Institution
from app.db.models.user import User
from app.db.session import get_db_session

router = APIRouter(prefix="/constraints", tags=["Constraints"])


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


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ConstraintResponse)
async def create_constraint(
    data: ConstraintCreate,
    institution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ConstraintResponse:
    """Create a new constraint."""
    await verify_institution_access(institution_id, current_user, db)
    constraint = Constraint(
        id=uuid4(),
        institution_id=institution_id,
        constraint_type=data.constraint_type,
        constraint_data=data.constraint_data,
        priority=data.priority or 1,
    )
    db.add(constraint)
    await db.commit()
    await db.refresh(constraint)
    return ConstraintResponse.model_validate(constraint)


@router.get("", response_model=list[ConstraintResponse])
async def list_constraints(
    institution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ConstraintResponse]:
    """Get list of constraints."""
    await verify_institution_access(institution_id, current_user, db)
    result = await db.execute(
        select(Constraint).where(Constraint.institution_id == institution_id)
    )
    constraints = result.scalars().all()
    return [ConstraintResponse.model_validate(c) for c in constraints]


@router.get("/{constraint_id}", response_model=ConstraintResponse)
async def get_constraint(
    constraint_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ConstraintResponse:
    """Get constraint by ID."""
    result = await db.execute(
        select(Constraint)
        .join(Institution)
        .where(Constraint.id == constraint_id, Institution.user_id == current_user.id)
    )
    constraint = result.scalar_one_or_none()
    if not constraint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Constraint not found"
        )
    return ConstraintResponse.model_validate(constraint)


@router.put("/{constraint_id}", response_model=ConstraintResponse)
async def update_constraint(
    constraint_id: UUID,
    data: ConstraintUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ConstraintResponse:
    """Update constraint."""
    result = await db.execute(
        select(Constraint)
        .join(Institution)
        .where(Constraint.id == constraint_id, Institution.user_id == current_user.id)
    )
    constraint = result.scalar_one_or_none()
    if not constraint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Constraint not found"
        )
    if data.constraint_type is not None:
        constraint.constraint_type = data.constraint_type
    if data.constraint_data is not None:
        constraint.constraint_data = data.constraint_data
    if data.priority is not None:
        constraint.priority = data.priority
    await db.commit()
    await db.refresh(constraint)
    return ConstraintResponse.model_validate(constraint)


@router.delete("/{constraint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_constraint(
    constraint_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete constraint."""
    result = await db.execute(
        select(Constraint)
        .join(Institution)
        .where(Constraint.id == constraint_id, Institution.user_id == current_user.id)
    )
    constraint = result.scalar_one_or_none()
    if not constraint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Constraint not found"
        )
    await db.delete(constraint)
    await db.commit()
