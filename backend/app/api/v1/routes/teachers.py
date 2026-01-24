"""API routes for managing teachers."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.teacher import (
    TeacherCreate,
    TeacherLessonAssign,
    TeacherLessonResponse,
    TeacherResponse,
    TeacherUpdate,
)
from app.core.dependencies import get_current_user
from app.db.models.institution import Institution
from app.db.models.lesson import Lesson
from app.db.models.teacher import Teacher
from app.db.models.teacher_lesson import TeacherLesson
from app.db.models.user import User
from app.db.session import get_db_session

router = APIRouter(prefix="/teachers", tags=["Teachers"])


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


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TeacherResponse)
async def create_teacher(
    data: TeacherCreate,
    institution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> TeacherResponse:
    """Create a new teacher."""
    await verify_institution_access(institution_id, current_user, db)
    teacher = Teacher(
        institution_id=institution_id,
        full_name=data.full_name,
        subject=data.subject,
    )
    db.add(teacher)
    await db.commit()
    await db.refresh(teacher)
    return TeacherResponse.model_validate(teacher)


@router.get("", response_model=list[TeacherResponse])
async def list_teachers(
    institution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[TeacherResponse]:
    """Get list of teachers."""
    await verify_institution_access(institution_id, current_user, db)
    result = await db.execute(
        select(Teacher).where(Teacher.institution_id == institution_id)
    )
    teachers = result.scalars().all()
    return [TeacherResponse.model_validate(teacher) for teacher in teachers]


@router.get("/{teacher_id}", response_model=TeacherResponse)
async def get_teacher(
    teacher_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> TeacherResponse:
    """Get teacher by ID."""
    result = await db.execute(
        select(Teacher)
        .join(Institution)
        .where(Teacher.id == teacher_id, Institution.user_id == current_user.id)
    )
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found"
        )
    return TeacherResponse.model_validate(teacher)


@router.put("/{teacher_id}", response_model=TeacherResponse)
async def update_teacher(
    teacher_id: int,
    data: TeacherUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> TeacherResponse:
    """Update teacher."""
    result = await db.execute(
        select(Teacher)
        .join(Institution)
        .where(Teacher.id == teacher_id, Institution.user_id == current_user.id)
    )
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found"
        )
    if data.full_name is not None:
        teacher.full_name = data.full_name
    if data.subject is not None:
        teacher.subject = data.subject
    await db.commit()
    await db.refresh(teacher)
    return TeacherResponse.model_validate(teacher)


@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_teacher(
    teacher_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete teacher."""
    result = await db.execute(
        select(Teacher)
        .join(Institution)
        .where(Teacher.id == teacher_id, Institution.user_id == current_user.id)
    )
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found"
        )
    await db.delete(teacher)
    await db.commit()


@router.post(
    "/{teacher_id}/assign-lessons",
    status_code=status.HTTP_201_CREATED,
    response_model=list[TeacherLessonResponse],
)
async def assign_lessons_to_teacher(
    teacher_id: int,
    data: TeacherLessonAssign,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[TeacherLessonResponse]:
    """Assign lessons to teacher."""
    result = await db.execute(
        select(Teacher)
        .join(Institution)
        .where(Teacher.id == teacher_id, Institution.user_id == current_user.id)
    )
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found"
        )
    result = await db.execute(
        select(Lesson).where(
            Lesson.id.in_(data.lesson_ids),
            Lesson.institution_id == teacher.institution_id,
        )
    )
    lessons = result.scalars().all()
    if len(lessons) != len(data.lesson_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some lessons not found or belong to different institution",
        )
    existing = await db.execute(
        select(TeacherLesson).where(TeacherLesson.teacher_id == teacher_id)
    )
    for existing_assignment in existing.scalars().all():
        await db.delete(existing_assignment)
    assignments = []
    for lesson_id in data.lesson_ids:
        assignment = TeacherLesson(
            id=uuid4(),
            teacher_id=teacher_id,
            lesson_id=lesson_id,
        )
        db.add(assignment)
        assignments.append(assignment)

    await db.commit()
    for assignment in assignments:
        await db.refresh(assignment)

    return [TeacherLessonResponse.model_validate(a) for a in assignments]


@router.get("/{teacher_id}/lessons", response_model=list[TeacherLessonResponse])
async def get_teacher_lessons(
    teacher_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[TeacherLessonResponse]:
    """Get list of teacher's lessons."""
    result = await db.execute(
        select(Teacher)
        .join(Institution)
        .where(Teacher.id == teacher_id, Institution.user_id == current_user.id)
    )
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found"
        )

    result = await db.execute(
        select(TeacherLesson).where(TeacherLesson.teacher_id == teacher_id)
    )
    assignments = result.scalars().all()
    return [TeacherLessonResponse.model_validate(a) for a in assignments]
