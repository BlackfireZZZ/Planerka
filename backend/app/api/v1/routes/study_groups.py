"""API routes for managing study groups."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.study_group import (
    StudyGroupCreate,
    StudyGroupLessonAssign,
    StudyGroupLessonLink,
    StudyGroupResponse,
    StudyGroupUpdate,
)
from app.core.dependencies import get_current_user
from app.db.models.institution import Institution
from app.db.models.lesson import Lesson
from app.db.models.student import Student
from app.db.models.stream import Stream
from app.db.models.study_group import StudyGroup, study_group_lessons, study_group_student
from app.db.models.user import User
from app.db.session import get_db_session

router = APIRouter(prefix="/study-groups", tags=["Study Groups"])


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


async def verify_students_in_stream(
    student_ids: list[UUID], stream_id: UUID, institution_id: UUID, db: AsyncSession
) -> None:
    """Verify that all students belong to class groups in the stream."""
    from app.db.models.class_group import ClassGroup
    from app.db.models.stream import stream_class_group
    result = await db.execute(
        select(ClassGroup.id)
        .join(stream_class_group)
        .where(stream_class_group.c.stream_id == stream_id)
    )
    stream_class_group_ids = {row[0] for row in result.all()}
    
    if not stream_class_group_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stream has no class groups",
        )
    result = await db.execute(
        select(Student).where(
            Student.id.in_(student_ids),
            Student.institution_id == institution_id,
            Student.class_group_id.in_(stream_class_group_ids),
        )
    )
    students = result.scalars().all()
    if len(students) != len(student_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some students not found or don't belong to class groups in this stream",
        )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=StudyGroupResponse)
async def create_study_group(
    data: StudyGroupCreate,
    institution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> StudyGroupResponse:
    """Create a new study group."""
    await verify_institution_access(institution_id, current_user, db)
    result = await db.execute(
        select(Stream).where(
            Stream.id == data.stream_id, Stream.institution_id == institution_id
        )
    )
    stream = result.scalar_one_or_none()
    if not stream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Stream not found"
        )
    if data.student_ids:
        await verify_students_in_stream(
            data.student_ids, data.stream_id, institution_id, db
        )
    
    study_group = StudyGroup(
        id=uuid4(),
        institution_id=institution_id,
        stream_id=data.stream_id,
        name=data.name,
    )
    db.add(study_group)
    await db.flush()
    if data.student_ids:
        for student_id in data.student_ids:
            await db.execute(
                study_group_student.insert().values(
                    study_group_id=study_group.id, student_id=student_id
                )
            )
    
    await db.commit()
    await db.refresh(study_group)
    result = await db.execute(
        select(Student)
        .join(study_group_student)
        .where(study_group_student.c.study_group_id == study_group.id)
    )
    students = result.scalars().all()
    
    response = StudyGroupResponse(
        id=study_group.id,
        institution_id=study_group.institution_id,
        stream_id=study_group.stream_id,
        name=study_group.name,
        created_at=study_group.created_at,
        updated_at=study_group.updated_at,
        students=[
            {"id": str(s.id), "full_name": s.full_name, "student_number": s.student_number}
            for s in students
        ],
    )
    return response


@router.get("", response_model=list[StudyGroupResponse])
async def list_study_groups(
    institution_id: UUID,
    stream_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[StudyGroupResponse]:
    """Get list of study groups."""
    await verify_institution_access(institution_id, current_user, db)
    
    query = select(StudyGroup).where(StudyGroup.institution_id == institution_id)
    if stream_id:
        query = query.where(StudyGroup.stream_id == stream_id)
    
    result = await db.execute(query)
    study_groups = result.scalars().all()
    
    responses = []
    for study_group in study_groups:
        result = await db.execute(
            select(Student)
            .join(study_group_student)
            .where(study_group_student.c.study_group_id == study_group.id)
        )
        students = result.scalars().all()
        response = StudyGroupResponse(
            id=study_group.id,
            institution_id=study_group.institution_id,
            stream_id=study_group.stream_id,
            name=study_group.name,
            created_at=study_group.created_at,
            updated_at=study_group.updated_at,
            students=[
                {"id": str(s.id), "full_name": s.full_name, "student_number": s.student_number}
                for s in students
            ],
        )
        responses.append(response)
    
    return responses


@router.get("/{study_group_id}", response_model=StudyGroupResponse)
async def get_study_group(
    study_group_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> StudyGroupResponse:
    """Get study group by ID."""
    result = await db.execute(
        select(StudyGroup)
        .join(Institution)
        .where(StudyGroup.id == study_group_id, Institution.user_id == current_user.id)
    )
    study_group = result.scalar_one_or_none()
    if not study_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Study group not found"
        )
    result = await db.execute(
        select(Student)
        .join(study_group_student)
        .where(study_group_student.c.study_group_id == study_group.id)
    )
    students = result.scalars().all()
    
    response = StudyGroupResponse(
        id=study_group.id,
        institution_id=study_group.institution_id,
        stream_id=study_group.stream_id,
        name=study_group.name,
        created_at=study_group.created_at,
        updated_at=study_group.updated_at,
        students=[
            {"id": str(s.id), "full_name": s.full_name, "student_number": s.student_number}
            for s in students
        ],
    )
    return response


@router.put("/{study_group_id}", response_model=StudyGroupResponse)
async def update_study_group(
    study_group_id: UUID,
    data: StudyGroupUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> StudyGroupResponse:
    """Update study group."""
    result = await db.execute(
        select(StudyGroup)
        .join(Institution)
        .where(StudyGroup.id == study_group_id, Institution.user_id == current_user.id)
    )
    study_group = result.scalar_one_or_none()
    if not study_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Study group not found"
        )
    
    if data.name is not None:
        study_group.name = data.name
    
    if data.stream_id is not None:
        result = await db.execute(
            select(Stream).where(
                Stream.id == data.stream_id,
                Stream.institution_id == study_group.institution_id,
            )
        )
        stream = result.scalar_one_or_none()
        if not stream:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Stream not found"
            )
        study_group.stream_id = data.stream_id
    if data.student_ids is not None:
        stream_id = data.stream_id or study_group.stream_id
        if data.student_ids:
            await verify_students_in_stream(
                data.student_ids, stream_id, study_group.institution_id, db
            )
        await db.execute(
            study_group_student.delete().where(
                study_group_student.c.study_group_id == study_group.id
            )
        )
        if data.student_ids:
            for student_id in data.student_ids:
                await db.execute(
                    study_group_student.insert().values(
                        study_group_id=study_group.id, student_id=student_id
                    )
                )
    
    await db.commit()
    await db.refresh(study_group)
    result = await db.execute(
        select(Student)
        .join(study_group_student)
        .where(study_group_student.c.study_group_id == study_group.id)
    )
    students = result.scalars().all()
    
    response = StudyGroupResponse(
        id=study_group.id,
        institution_id=study_group.institution_id,
        stream_id=study_group.stream_id,
        name=study_group.name,
        created_at=study_group.created_at,
        updated_at=study_group.updated_at,
        students=[
            {"id": str(s.id), "full_name": s.full_name, "student_number": s.student_number}
            for s in students
        ],
    )
    return response


@router.delete("/{study_group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_study_group(
    study_group_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete study group."""
    result = await db.execute(
        select(StudyGroup)
        .join(Institution)
        .where(StudyGroup.id == study_group_id, Institution.user_id == current_user.id)
    )
    study_group = result.scalar_one_or_none()
    if not study_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Study group not found"
        )
    await db.delete(study_group)
    await db.commit()


@router.post(
    "/{study_group_id}/assign-lessons",
    status_code=status.HTTP_201_CREATED,
    response_model=list[StudyGroupLessonLink],
)
async def assign_lessons_to_study_group(
    study_group_id: UUID,
    data: StudyGroupLessonAssign,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[StudyGroupLessonLink]:
    """Assign lessons to a study group."""
    result = await db.execute(
        select(StudyGroup)
        .join(Institution)
        .where(
            StudyGroup.id == study_group_id, Institution.user_id == current_user.id
        )
    )
    study_group = result.scalar_one_or_none()
    if not study_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Study group not found"
        )
    if data.lesson_ids:
        lessons_result = await db.execute(
            select(Lesson).where(
                Lesson.id.in_(data.lesson_ids),
                Lesson.institution_id == study_group.institution_id,
            )
        )
        lessons = lessons_result.scalars().all()
        if len(lessons) != len(data.lesson_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some lessons not found or belong to different institution",
            )
    await db.execute(
        study_group_lessons.delete().where(
            study_group_lessons.c.study_group_id == study_group_id
        )
    )
    for lesson_id in data.lesson_ids:
        await db.execute(
            study_group_lessons.insert().values(
                study_group_id=study_group_id, lesson_id=lesson_id
            )
        )
    await db.commit()
    return [StudyGroupLessonLink(lesson_id=lid) for lid in data.lesson_ids]


@router.get(
    "/{study_group_id}/lessons", response_model=list[StudyGroupLessonLink]
)
async def get_study_group_lessons(
    study_group_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[StudyGroupLessonLink]:
    """Get list of lessons assigned to a study group."""
    result = await db.execute(
        select(StudyGroup)
        .join(Institution)
        .where(
            StudyGroup.id == study_group_id, Institution.user_id == current_user.id
        )
    )
    study_group = result.scalar_one_or_none()
    if not study_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Study group not found"
        )
    lessons_result = await db.execute(
        select(study_group_lessons.c.lesson_id).where(
            study_group_lessons.c.study_group_id == study_group_id
        )
    )
    return [
        StudyGroupLessonLink(lesson_id=row.lesson_id)
        for row in lessons_result.all()
    ]
