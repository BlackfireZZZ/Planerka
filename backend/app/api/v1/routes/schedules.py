"""
API routes for managing schedules.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.schedule import (
    ScheduleCreate,
    ScheduleEntryResponse,
    ScheduleGenerateRequest,
    ScheduleGenerateResponse,
    ScheduleResponse,
    ScheduleUpdate,
)
from app.core.dependencies import get_current_user
from app.db.models.institution import Institution
from app.db.models.schedule import Schedule
from app.db.models.schedule_entry import ScheduleEntry
from app.db.models.user import User
from app.db.session import get_db_session
from app.export.pdf_generator import PDFScheduleExporter
from app.scheduler.schedule_generator import ScheduleGenerator
from app.storage.s3 import get_s3_client

router = APIRouter(prefix="/schedules", tags=["Schedules"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ScheduleResponse)
async def create_schedule(
    data: ScheduleCreate,
    institution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ScheduleResponse:
    """Create a new schedule."""
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

    schedule = Schedule(
        id=uuid4(),
        institution_id=institution_id,
        name=data.name,
        academic_period=data.academic_period,
        status="draft",
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return ScheduleResponse.model_validate(schedule)


@router.get("", response_model=list[ScheduleResponse])
async def list_schedules(
    institution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ScheduleResponse]:
    """Get list of institution schedules."""
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

    result = await db.execute(
        select(Schedule).where(Schedule.institution_id == institution_id)
    )
    schedules = result.scalars().all()
    if not schedules:
        return []

    # Один запрос на кол-во записей, без загрузки schedule.entries
    ids = [s.id for s in schedules]
    counts_result = await db.execute(
        select(ScheduleEntry.schedule_id, func.count(ScheduleEntry.id).label("c"))
        .where(ScheduleEntry.schedule_id.in_(ids))
        .group_by(ScheduleEntry.schedule_id)
    )
    counts = {row.schedule_id: row.c for row in counts_result.all()}

    return [
        ScheduleResponse(
            id=s.id,
            institution_id=s.institution_id,
            name=s.name,
            academic_period=s.academic_period,
            status=s.status,
            generated_at=s.generated_at,
            created_at=s.created_at,
            updated_at=s.updated_at,
            entries=[],
            entries_count=counts.get(s.id, 0),
        )
        for s in schedules
    ]


@router.get("/{schedule_id}/with-references")
async def get_schedule_with_references(
    schedule_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Расписание и все справочники учреждения одним запросом (вместо 8 HTTP)."""
    from app.api.v1.schemas.class_group import ClassGroupResponse
    from app.api.v1.schemas.lesson import LessonResponse
    from app.api.v1.schemas.room import RoomResponse
    from app.api.v1.schemas.student import StudentResponse
    from app.api.v1.schemas.study_group import StudyGroupResponse
    from app.api.v1.schemas.teacher import TeacherResponse
    from app.api.v1.schemas.time_slot import TimeSlotResponse

    from app.db.models import (
        ClassGroup,
        Lesson,
        Room,
        Student,
        StudyGroup,
        Teacher,
        TimeSlot,
    )
    from app.db.models.study_group import study_group_student

    result = await db.execute(
        select(Schedule)
        .join(Institution)
        .where(Schedule.id == schedule_id, Institution.user_id == current_user.id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )
    iid = schedule.institution_id

    entries_result = await db.execute(
        select(ScheduleEntry).where(ScheduleEntry.schedule_id == schedule_id)
    )
    entries = entries_result.scalars().all()

    schedule_dict = {
        "id": schedule.id,
        "institution_id": schedule.institution_id,
        "name": schedule.name,
        "academic_period": schedule.academic_period,
        "status": schedule.status,
        "generated_at": schedule.generated_at,
        "created_at": schedule.created_at,
        "updated_at": schedule.updated_at,
        "entries": [ScheduleEntryResponse.model_validate(e) for e in entries],
    }

    ts = (await db.execute(select(TimeSlot).where(TimeSlot.institution_id == iid))).scalars().all()
    les = (await db.execute(select(Lesson).where(Lesson.institution_id == iid))).scalars().all()
    tch = (await db.execute(select(Teacher).where(Teacher.institution_id == iid))).scalars().all()
    rm = (await db.execute(select(Room).where(Room.institution_id == iid))).scalars().all()
    cg = (await db.execute(select(ClassGroup).where(ClassGroup.institution_id == iid))).scalars().all()
    sg = (await db.execute(select(StudyGroup).where(StudyGroup.institution_id == iid))).scalars().all()
    st = (await db.execute(select(Student).where(Student.institution_id == iid))).scalars().all()

    sg_ids = [s.id for s in sg]
    sg_to_students: dict = {}
    if sg_ids:
        sgs_result = await db.execute(
            select(Student, study_group_student.c.study_group_id)
            .select_from(Student)
            .join(study_group_student, Student.id == study_group_student.c.student_id)
            .where(study_group_student.c.study_group_id.in_(sg_ids))
        )
        for row in sgs_result.all():
            student, sgg_id = row[0], row[1]
            sg_to_students.setdefault(sgg_id, []).append(
                {"id": str(student.id), "full_name": student.full_name, "student_number": student.student_number}
            )

    study_groups_data = [
        StudyGroupResponse(
            id=s.id,
            institution_id=s.institution_id,
            stream_id=s.stream_id,
            name=s.name,
            created_at=s.created_at,
            updated_at=s.updated_at,
            students=sg_to_students.get(s.id, []),
        )
        for s in sg
    ]

    return {
        "schedule": ScheduleResponse.model_validate(schedule_dict),
        "time_slots": [TimeSlotResponse.model_validate(x) for x in ts],
        "lessons": [LessonResponse.model_validate(x) for x in les],
        "teachers": [TeacherResponse.model_validate(x) for x in tch],
        "rooms": [RoomResponse.model_validate(x) for x in rm],
        "class_groups": [ClassGroupResponse.model_validate(x) for x in cg],
        "study_groups": study_groups_data,
        "students": [StudentResponse.model_validate(x) for x in st],
    }


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ScheduleResponse:
    """Get schedule by ID with entries."""
    result = await db.execute(
        select(Schedule)
        .join(Institution)
        .where(Schedule.id == schedule_id, Institution.user_id == current_user.id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )
    entries_result = await db.execute(
        select(ScheduleEntry).where(ScheduleEntry.schedule_id == schedule_id)
    )
    entries = entries_result.scalars().all()

    # Собираем ответ вручную, чтобы не обращаться к schedule.entries
    # (это запускает лишний selectin и каскадные загрузки)
    schedule_dict = {
        "id": schedule.id,
        "institution_id": schedule.institution_id,
        "name": schedule.name,
        "academic_period": schedule.academic_period,
        "status": schedule.status,
        "generated_at": schedule.generated_at,
        "created_at": schedule.created_at,
        "updated_at": schedule.updated_at,
        "entries": [ScheduleEntryResponse.model_validate(e) for e in entries],
    }
    return ScheduleResponse.model_validate(schedule_dict)


@router.post("/{schedule_id}/generate", response_model=ScheduleGenerateResponse)
async def generate_schedule(
    schedule_id: UUID,
    request: ScheduleGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ScheduleGenerateResponse:
    """Generate schedule using SAT solver."""
    result = await db.execute(
        select(Schedule)
        .join(Institution)
        .where(Schedule.id == schedule_id, Institution.user_id == current_user.id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )
    generator = ScheduleGenerator(db)
    success, schedule_entries, error = await generator.generate(
        schedule.institution_id, timeout=request.timeout
    )

    if not success:
        return ScheduleGenerateResponse(
            success=False, message=error or "Generation failed", entries_count=None
        )
    result = await db.execute(
        select(ScheduleEntry).where(ScheduleEntry.schedule_id == schedule_id)
    )
    old_entries = result.scalars().all()
    for entry in old_entries:
        await db.delete(entry)
    for entry_data in schedule_entries:
        entry = ScheduleEntry(
            id=uuid4(),
            institution_id=schedule.institution_id,
            schedule_id=schedule_id,
            lesson_id=entry_data["lesson_id"],
            teacher_id=entry_data["teacher_id"],
            class_group_id=entry_data.get("class_group_id"),
            study_group_id=entry_data.get("study_group_id"),
            room_id=entry_data["room_id"],
            time_slot_id=entry_data["time_slot_id"],
        )
        db.add(entry)
    schedule.status = "generated"
    schedule.generated_at = datetime.now(timezone.utc)

    await db.commit()

    return ScheduleGenerateResponse(
        success=True,
        message="Schedule generated successfully",
        entries_count=len(schedule_entries),
    )


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: UUID,
    data: ScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ScheduleResponse:
    """Update schedule."""
    result = await db.execute(
        select(Schedule)
        .join(Institution)
        .where(Schedule.id == schedule_id, Institution.user_id == current_user.id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )

    if data.name is not None:
        schedule.name = data.name
    if data.academic_period is not None:
        schedule.academic_period = data.academic_period
    if data.status is not None:
        schedule.status = data.status

    await db.commit()
    await db.refresh(schedule)
    return ScheduleResponse.model_validate(schedule)


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete schedule."""
    result = await db.execute(
        select(Schedule)
        .join(Institution)
        .where(Schedule.id == schedule_id, Institution.user_id == current_user.id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )

    await db.delete(schedule)
    await db.commit()


@router.get("/{schedule_id}/export/pdf")
async def export_schedule_pdf(
    schedule_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    s3_storage=Depends(get_s3_client),
) -> dict:
    """Export schedule to PDF and upload to S3, return pre-signed URL."""
    result = await db.execute(
        select(Schedule)
        .join(Institution)
        .where(Schedule.id == schedule_id, Institution.user_id == current_user.id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )
    from sqlalchemy.orm import selectinload

    from app.db.models import ClassGroup, Lesson, Room, Teacher, TimeSlot

    entries_result = await db.execute(
        select(ScheduleEntry)
        .where(ScheduleEntry.schedule_id == schedule_id)
        .options(
            selectinload(ScheduleEntry.lesson),
            selectinload(ScheduleEntry.teacher),
            selectinload(ScheduleEntry.class_group),
            selectinload(ScheduleEntry.study_group),
            selectinload(ScheduleEntry.room),
            selectinload(ScheduleEntry.time_slot),
        )
    )
    entries = entries_result.scalars().all()

    if not entries:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Schedule has no entries"
        )
    time_slots = {entry.time_slot_id: entry.time_slot for entry in entries}
    lessons = {entry.lesson_id: entry.lesson for entry in entries}
    teachers = {entry.teacher_id: entry.teacher for entry in entries}
    class_groups = {
        entry.class_group_id: entry.class_group
        for entry in entries
        if entry.class_group_id and entry.class_group
    }
    study_groups = {
        entry.study_group_id: entry.study_group
        for entry in entries
        if entry.study_group_id and entry.study_group
    }
    rooms = {entry.room_id: entry.room for entry in entries}
    exporter = PDFScheduleExporter()
    pdf_buffer = exporter.export_schedule(
        schedule_name=schedule.name,
        entries=entries,
        time_slots=time_slots,
        lessons=lessons,
        teachers=teachers,
        class_groups=class_groups,
        study_groups=study_groups,
        rooms=rooms,
    )
    pdf_bytes = pdf_buffer.read()
    object_key = f"schedules/{schedule_id}/schedule_{schedule_id}.pdf"
    await s3_storage.upload_bytes(
        pdf_bytes,
        object_key,
        content_type="application/pdf",
        metadata={
            "schedule_id": str(schedule_id),
            "schedule_name": schedule.name,
            "user_id": str(current_user.id),
        },
    )
    pre_signed_url = await s3_storage.get_file_url(object_key, expires_in=3600)

    return {
        "url": pre_signed_url,
        "filename": f"schedule_{schedule_id}.pdf",
    }
