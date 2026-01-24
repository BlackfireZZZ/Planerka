"""
Module for generating PDF schedules.
"""

from io import BytesIO
from typing import List
from uuid import UUID

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.db.models.schedule_entry import ScheduleEntry


class PDFScheduleExporter:
    """
    Class for exporting schedules to PDF.
    """

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Setup styles for PDF."""
        pass

    def export_schedule(
        self,
        schedule_name: str,
        entries: List[ScheduleEntry],
        time_slots: dict,
        lessons: dict,
        teachers: dict,
        class_groups: dict,
        study_groups: dict,
        rooms: dict,
    ) -> BytesIO:
        """
        Generates PDF for a complete schedule.

        Args:
            schedule_name: Schedule name
            entries: List of schedule entries
            time_slots: Dictionary {time_slot_id: time_slot_obj}
            lessons: Dictionary {lesson_id: lesson_obj}
            teachers: Dictionary {teacher_id: teacher_obj}
            class_groups: Dictionary {class_group_id: class_group_obj}
            study_groups: Dictionary {study_group_id: study_group_obj}
            rooms: Dictionary {room_id: room_obj}

        Returns:
            BytesIO object with PDF content
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
        story = []
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=self.styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1a1a1a"),
            spaceAfter=30,
        )
        story.append(Paragraph(schedule_name, title_style))
        story.append(Spacer(1, 0.5 * cm))
        days = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        day_entries = {day: [] for day in days}

        for entry in entries:
            time_slot = time_slots.get(entry.time_slot_id)
            if time_slot:
                day_name = days[time_slot.day_of_week]
                day_entries[day_name].append(entry)
        for day_name in days:
            if not day_entries[day_name]:
                continue
            day_style = ParagraphStyle(
                "DayTitle",
                parent=self.styles["Heading2"],
                fontSize=16,
                textColor=colors.HexColor("#2c3e50"),
                spaceAfter=10,
            )
            story.append(Paragraph(day_name, day_style))
            day_entries[day_name].sort(
                key=lambda e: (
                    time_slots.get(e.time_slot_id).start_time
                    if time_slots.get(e.time_slot_id)
                    else None
                )
            )
            table_data = [["Time", "Subject", "Teacher", "Group", "Room"]]

            for entry in day_entries[day_name]:
                time_slot = time_slots.get(entry.time_slot_id)
                lesson = lessons.get(entry.lesson_id)
                teacher = teachers.get(entry.teacher_id)
                class_group = class_groups.get(entry.class_group_id) if entry.class_group_id else None
                study_group = study_groups.get(entry.study_group_id) if entry.study_group_id else None
                room = rooms.get(entry.room_id)

                time_str = (
                    f"{time_slot.start_time.strftime('%H:%M')}-{time_slot.end_time.strftime('%H:%M')}"
                    if time_slot
                    else ""
                )
                lesson_name = lesson.name if lesson else ""
                teacher_name = teacher.full_name if teacher else ""
                if class_group:
                    group_name = class_group.name
                elif study_group:
                    group_name = f"{study_group.name} (Study Group)"
                else:
                    group_name = ""
                room_name = room.name if room else ""

                table_data.append(
                    [time_str, lesson_name, teacher_name, group_name, room_name]
                )

            table = Table(
                table_data, colWidths=[3 * cm, 4 * cm, 4 * cm, 3 * cm, 3 * cm]
            )
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 12),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.lightgrey],
                        ),
                    ]
                )
            )
            story.append(table)
            story.append(Spacer(1, 0.5 * cm))

        doc.build(story)
        buffer.seek(0)
        return buffer

    def export_for_teacher(
        self,
        teacher_name: str,
        entries: List[ScheduleEntry],
        time_slots: dict,
        lessons: dict,
        class_groups: dict,
        rooms: dict,
    ) -> BytesIO:
        """Generates PDF schedule for a teacher."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []

        title_style = ParagraphStyle(
            "CustomTitle",
            parent=self.styles["Heading1"],
            fontSize=20,
            textColor=colors.HexColor("#1a1a1a"),
            spaceAfter=20,
        )
        story.append(Paragraph(f"Schedule: {teacher_name}", title_style))
        story.append(Spacer(1, 0.5 * cm))
        days = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        day_entries = {day: [] for day in days}

        for entry in entries:
            time_slot = time_slots.get(entry.time_slot_id)
            if time_slot:
                day_name = days[time_slot.day_of_week]
                day_entries[day_name].append(entry)

        for day_name in days:
            if not day_entries[day_name]:
                continue

            day_style = ParagraphStyle(
                "DayTitle",
                parent=self.styles["Heading2"],
                fontSize=14,
                textColor=colors.HexColor("#2c3e50"),
            )
            story.append(Paragraph(day_name, day_style))

            table_data = [["Time", "Subject", "Group", "Room"]]
            for entry in day_entries[day_name]:
                time_slot = time_slots.get(entry.time_slot_id)
                lesson = lessons.get(entry.lesson_id)
                class_group = class_groups.get(entry.class_group_id)
                room = rooms.get(entry.room_id)

                time_str = (
                    f"{time_slot.start_time.strftime('%H:%M')}-{time_slot.end_time.strftime('%H:%M')}"
                    if time_slot
                    else ""
                )
                table_data.append(
                    [
                        time_str,
                        lesson.name if lesson else "",
                        class_group.name if class_group else "",
                        room.name if room else "",
                    ]
                )

            table = Table(table_data, colWidths=[3 * cm, 5 * cm, 4 * cm, 3 * cm])
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            story.append(table)
            story.append(Spacer(1, 0.3 * cm))

        doc.build(story)
        buffer.seek(0)
        return buffer

    def export_for_class(
        self,
        class_name: str,
        entries: List[ScheduleEntry],
        time_slots: dict,
        lessons: dict,
        teachers: dict,
        rooms: dict,
    ) -> BytesIO:
        """Generates PDF schedule for a class."""
        return self.export_for_teacher(
            class_name, entries, time_slots, lessons, teachers, rooms
        )

    def export_for_room(
        self,
        room_name: str,
        entries: List[ScheduleEntry],
        time_slots: dict,
        lessons: dict,
        teachers: dict,
        class_groups: dict,
    ) -> BytesIO:
        """Generates PDF schedule for a room."""
        return self.export_for_teacher(
            room_name, entries, time_slots, lessons, teachers, class_groups
        )

    def export_for_student(
        self,
        student_name: str,
        entries: List[ScheduleEntry],
        time_slots: dict,
        lessons: dict,
        teachers: dict,
        rooms: dict,
    ) -> BytesIO:
        """Generates PDF schedule for a student."""
        return self.export_for_teacher(
            student_name, entries, time_slots, lessons, teachers, rooms
        )
