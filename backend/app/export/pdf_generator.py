"""
Module for generating PDF schedules.
"""

import logging
import os
from io import BytesIO
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.db.models.schedule_entry import ScheduleEntry

logger = logging.getLogger(__name__)

# Имена шрифтов с поддержкой кириллицы (после регистрации)
_FONT_REG = "PdfCyrillic"
_FONT_BOLD = "PdfCyrillic-Bold"
_cyrillic_fonts_registered: bool | None = (
    None  # None=ещё не пробовали, True/False=результат
)


def _register_cyrillic_fonts() -> bool:
    """Регистрирует шрифты с поддержкой кириллицы. Возвращает True при успехе."""
    global _cyrillic_fonts_registered
    if _cyrillic_fonts_registered is not None:
        return _cyrillic_fonts_registered
    # DejaVu (Linux/Docker, пакет fonts-dejavu-core)
    paths_reg = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]
    paths_bold = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]
    # Arial (Windows)
    win = os.environ.get("WINDIR", "C:\\Windows")
    paths_reg.append(os.path.join(win, "Fonts", "arial.ttf"))
    paths_bold.append(os.path.join(win, "Fonts", "arialbd.ttf"))

    reg_path = None
    for p in paths_reg:
        if os.path.isfile(p):
            try:
                pdfmetrics.registerFont(TTFont(_FONT_REG, p))
                reg_path = p
                break
            except Exception as e:
                logger.warning("Не удалось загрузить шрифт %s: %s", p, e)
    if not reg_path:
        logger.warning(
            "Шрифт с кириллицей не найден. Кириллица в PDF может отображаться некорректно."
        )
        _cyrillic_fonts_registered = False
        return False

    for p in paths_bold:
        if os.path.isfile(p):
            try:
                pdfmetrics.registerFont(TTFont(_FONT_BOLD, p))
                break
            except Exception as e:
                logger.warning("Не удалось загрузить жирный шрифт %s: %s", p, e)
    else:
        # жирный не найден — используем тот же файл, что и для обычного
        try:
            pdfmetrics.registerFont(TTFont(_FONT_BOLD, reg_path))
        except Exception:
            pass
    _cyrillic_fonts_registered = True
    return True


class PDFScheduleExporter:
    """
    Class for exporting schedules to PDF.
    """

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._cyrillic_ok = _register_cyrillic_fonts()
        self._font = _FONT_REG if self._cyrillic_ok else "Helvetica"
        self._font_bold = _FONT_BOLD if self._cyrillic_ok else "Helvetica-Bold"
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
        margin = 1.2 * cm
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            leftMargin=margin,
            rightMargin=margin,
            topMargin=margin,
            bottomMargin=margin,
        )
        story = []
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=self.styles["Heading1"],
            fontName=self._font,
            fontSize=22,
            textColor=colors.HexColor("#1a1a1a"),
            spaceAfter=20,
        )
        story.append(Paragraph(schedule_name, title_style))
        story.append(Spacer(1, 0.4 * cm))
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
                fontName=self._font,
                fontSize=14,
                textColor=colors.HexColor("#2c3e50"),
                spaceAfter=8,
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
                class_group = (
                    class_groups.get(entry.class_group_id)
                    if entry.class_group_id
                    else None
                )
                study_group = (
                    study_groups.get(entry.study_group_id)
                    if entry.study_group_id
                    else None
                )
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
                table_data,
                colWidths=[2.8 * cm, 3.8 * cm, 3.8 * cm, 2.8 * cm, 2.8 * cm],
                repeatRows=1,
            )
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), self._font_bold),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                        ("TOPPADDING", (0, 0), (-1, 0), 8),
                        ("FONTNAME", (0, 1), (-1, -1), self._font),
                        ("FONTSIZE", (0, 1), (-1, -1), 9),
                        ("TOPPADDING", (0, 1), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
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
            story.append(Spacer(1, 0.4 * cm))

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
        margin = 1.2 * cm
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=margin,
            rightMargin=margin,
            topMargin=margin,
            bottomMargin=margin,
        )
        story = []

        title_style = ParagraphStyle(
            "CustomTitle",
            parent=self.styles["Heading1"],
            fontName=self._font,
            fontSize=18,
            textColor=colors.HexColor("#1a1a1a"),
            spaceAfter=16,
        )
        story.append(Paragraph(f"Schedule: {teacher_name}", title_style))
        story.append(Spacer(1, 0.4 * cm))
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
                fontName=self._font,
                fontSize=12,
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

            table = Table(
                table_data,
                colWidths=[2.8 * cm, 6 * cm, 4 * cm, 2.8 * cm],
                repeatRows=1,
            )
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), self._font_bold),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("FONTNAME", (0, 1), (-1, -1), self._font),
                        ("FONTSIZE", (0, 1), (-1, -1), 9),
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
