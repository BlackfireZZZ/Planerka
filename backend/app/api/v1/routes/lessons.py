"""API routes for managing lessons."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.lesson import LessonCreate, LessonResponse, LessonUpdate
from app.core.dependencies import get_current_user
from app.db.models.institution import Institution
from app.db.models.lesson import Lesson
from app.db.models.user import User
from app.db.session import get_db_session

router = APIRouter(prefix="/lessons", tags=["Lessons"])


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


@router.post("", status_code=status.HTTP_201_CREATED, response_model=LessonResponse)
async def create_lesson(
    data: LessonCreate,
    institution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> LessonResponse:
    """Create a new lesson."""
    await verify_institution_access(institution_id, current_user, db)
    lesson = Lesson(
        id=uuid4(),
        institution_id=institution_id,
        name=data.name,
        subject_code=data.subject_code,
        duration_minutes=data.duration_minutes,
    )
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    return LessonResponse.model_validate(lesson)


@router.get("", response_model=list[LessonResponse])
async def list_lessons(
    institution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[LessonResponse]:
    """Get list of lessons."""
    await verify_institution_access(institution_id, current_user, db)
    result = await db.execute(
        select(Lesson).where(Lesson.institution_id == institution_id)
    )
    lessons = result.scalars().all()
    return [LessonResponse.model_validate(lesson) for lesson in lessons]


@router.get("/{lesson_id}", response_model=LessonResponse)
async def get_lesson(
    lesson_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> LessonResponse:
    """Get lesson by ID."""
    result = await db.execute(
        select(Lesson)
        .join(Institution)
        .where(Lesson.id == lesson_id, Institution.user_id == current_user.id)
    )
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found"
        )
    return LessonResponse.model_validate(lesson)


@router.put("/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    lesson_id: UUID,
    data: LessonUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> LessonResponse:
    """Update lesson."""
    result = await db.execute(
        select(Lesson)
        .join(Institution)
        .where(Lesson.id == lesson_id, Institution.user_id == current_user.id)
    )
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found"
        )
    if data.name is not None:
        lesson.name = data.name
    if data.subject_code is not None:
        lesson.subject_code = data.subject_code
    if data.duration_minutes is not None:
        lesson.duration_minutes = data.duration_minutes
    await db.commit()
    await db.refresh(lesson)
    return LessonResponse.model_validate(lesson)


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete lesson."""
    result = await db.execute(
        select(Lesson)
        .join(Institution)
        .where(Lesson.id == lesson_id, Institution.user_id == current_user.id)
    )
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found"
        )
    await db.delete(lesson)
    await db.commit()
