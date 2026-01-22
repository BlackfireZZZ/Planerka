"""API routes for managing students."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.student import StudentCreate, StudentResponse, StudentUpdate
from app.core.dependencies import get_current_user
from app.db.models.institution import Institution
from app.db.models.student import Student
from app.db.models.user import User
from app.db.session import get_db_session

router = APIRouter(prefix="/students", tags=["Students"])


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


@router.post("", status_code=status.HTTP_201_CREATED, response_model=StudentResponse)
async def create_student(
    data: StudentCreate,
    institution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> StudentResponse:
    """Create a new student."""
    await verify_institution_access(institution_id, current_user, db)
    student = Student(
        id=uuid4(),
        institution_id=institution_id,
        class_group_id=data.class_group_id,
        full_name=data.full_name,
        student_number=data.student_number,
    )
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return StudentResponse.model_validate(student)


@router.get("", response_model=list[StudentResponse])
async def list_students(
    institution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[StudentResponse]:
    """Get list of students."""
    await verify_institution_access(institution_id, current_user, db)
    result = await db.execute(
        select(Student).where(Student.institution_id == institution_id)
    )
    students = result.scalars().all()
    return [StudentResponse.model_validate(student) for student in students]


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> StudentResponse:
    """Get student by ID."""
    result = await db.execute(
        select(Student)
        .join(Institution)
        .where(Student.id == student_id, Institution.user_id == current_user.id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )
    return StudentResponse.model_validate(student)


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: UUID,
    data: StudentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> StudentResponse:
    """Update student."""
    result = await db.execute(
        select(Student)
        .join(Institution)
        .where(Student.id == student_id, Institution.user_id == current_user.id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )
    if data.class_group_id is not None:
        student.class_group_id = data.class_group_id
    if data.full_name is not None:
        student.full_name = data.full_name
    if data.student_number is not None:
        student.student_number = data.student_number
    await db.commit()
    await db.refresh(student)
    return StudentResponse.model_validate(student)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete student."""
    result = await db.execute(
        select(Student)
        .join(Institution)
        .where(Student.id == student_id, Institution.user_id == current_user.id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )
    await db.delete(student)
    await db.commit()
