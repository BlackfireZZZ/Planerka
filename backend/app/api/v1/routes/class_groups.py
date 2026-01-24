"""API routes for managing class groups."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.class_group import (
    ClassGroupCreate,
    ClassGroupLessonAssign,
    ClassGroupLessonLink,
    ClassGroupResponse,
    ClassGroupUpdate,
)
from app.core.dependencies import get_current_user
from app.db.models.class_group import ClassGroup, class_group_lessons
from app.db.models.institution import Institution
from app.db.models.lesson import Lesson
from app.db.models.user import User
from app.db.session import get_db_session

router = APIRouter(prefix="/class-groups", tags=["Class Groups"])


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


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ClassGroupResponse)
async def create_class_group(
    data: ClassGroupCreate,
    institution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ClassGroupResponse:
    """Create a new class group."""
    await verify_institution_access(institution_id, current_user, db)
    group = ClassGroup(
        id=uuid4(),
        institution_id=institution_id,
        name=data.name,
        student_count=data.student_count,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return ClassGroupResponse.model_validate(group)


@router.get("", response_model=list[ClassGroupResponse])
async def list_class_groups(
    institution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ClassGroupResponse]:
    """Get list of class groups."""
    await verify_institution_access(institution_id, current_user, db)
    result = await db.execute(
        select(ClassGroup).where(ClassGroup.institution_id == institution_id)
    )
    groups = result.scalars().all()
    return [ClassGroupResponse.model_validate(g) for g in groups]


@router.get("/{group_id}", response_model=ClassGroupResponse)
async def get_class_group(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ClassGroupResponse:
    """Get class group by ID."""
    result = await db.execute(
        select(ClassGroup)
        .join(Institution)
        .where(ClassGroup.id == group_id, Institution.user_id == current_user.id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class group not found"
        )
    return ClassGroupResponse.model_validate(group)


@router.put("/{group_id}", response_model=ClassGroupResponse)
async def update_class_group(
    group_id: UUID,
    data: ClassGroupUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ClassGroupResponse:
    """Update class group."""
    result = await db.execute(
        select(ClassGroup)
        .join(Institution)
        .where(ClassGroup.id == group_id, Institution.user_id == current_user.id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class group not found"
        )
    if data.name is not None:
        group.name = data.name
    if data.student_count is not None:
        group.student_count = data.student_count
    await db.commit()
    await db.refresh(group)
    return ClassGroupResponse.model_validate(group)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class_group(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete class group."""
    result = await db.execute(
        select(ClassGroup)
        .join(Institution)
        .where(ClassGroup.id == group_id, Institution.user_id == current_user.id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class group not found"
        )
    await db.delete(group)
    await db.commit()


@router.post(
    "/{group_id}/assign-lessons",
    status_code=status.HTTP_201_CREATED,
    response_model=list[ClassGroupLessonLink],
)
async def assign_lessons_to_class_group(
    group_id: UUID,
    data: ClassGroupLessonAssign,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ClassGroupLessonLink]:
    """Assign lessons to a class group."""
    result = await db.execute(
        select(ClassGroup)
        .join(Institution)
        .where(ClassGroup.id == group_id, Institution.user_id == current_user.id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class group not found"
        )
    if data.lesson_ids:
        lessons_result = await db.execute(
            select(Lesson).where(
                Lesson.id.in_(data.lesson_ids),
                Lesson.institution_id == group.institution_id,
            )
        )
        lessons = lessons_result.scalars().all()
        if len(lessons) != len(data.lesson_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some lessons not found or belong to different institution",
            )
    await db.execute(
        class_group_lessons.delete().where(
            class_group_lessons.c.class_group_id == group_id
        )
    )
    for lesson_id in data.lesson_ids:
        await db.execute(
            class_group_lessons.insert().values(
                class_group_id=group_id, lesson_id=lesson_id
            )
        )
    await db.commit()
    return [ClassGroupLessonLink(lesson_id=lid) for lid in data.lesson_ids]


@router.get("/{group_id}/lessons", response_model=list[ClassGroupLessonLink])
async def get_class_group_lessons(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ClassGroupLessonLink]:
    """Get list of lessons assigned to a class group."""
    result = await db.execute(
        select(ClassGroup)
        .join(Institution)
        .where(ClassGroup.id == group_id, Institution.user_id == current_user.id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class group not found"
        )
    lessons_result = await db.execute(
        select(class_group_lessons.c.lesson_id).where(
            class_group_lessons.c.class_group_id == group_id
        )
    )
    return [ClassGroupLessonLink(lesson_id=row.lesson_id) for row in lessons_result.all()]
