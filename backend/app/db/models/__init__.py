"""
Import all models so that Base has them before being imported by Alembic.
"""

from app.db.base import Base

from .class_group import ClassGroup
from .constraint import Constraint
from .email_verification import EmailVerificationToken
from .institution import Institution
from .lesson import Lesson
from .password_reset import PasswordResetToken
from .room import Room
from .schedule import Schedule
from .schedule_entry import ScheduleEntry
from .session import Session
from .stream import Stream
from .student import Student
from .study_group import StudyGroup
from .teacher import Teacher
from .teacher_lesson import TeacherLesson
from .time_slot import TimeSlot
from .user import User

__all__ = [
    "Base",
    "ClassGroup",
    "Constraint",
    "EmailVerificationToken",
    "Institution",
    "Lesson",
    "PasswordResetToken",
    "Room",
    "Schedule",
    "ScheduleEntry",
    "Session",
    "Student",
    "StudyGroup",
    "Stream",
    "Teacher",
    "TeacherLesson",
    "TimeSlot",
    "User",
]
