import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  Calendar,
  Download,
  RefreshCw,
  ArrowLeft,
  Clock,
  Users,
  BookOpen,
  MapPin,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { schedulesApi } from "@/api/schedules";
import type { Schedule, ScheduleEntry, ScheduleGenerateRequest } from "@/api/schedules";
import type { TimeSlot } from "@/api/timeSlots";
import type { Lesson } from "@/api/lessons";
import type { Teacher } from "@/api/teachers";
import type { Room } from "@/api/rooms";
import type { ClassGroup } from "@/api/classGroups";
import type { StudyGroup } from "@/api/studyGroups";
import type { Student } from "@/api/students";

export const ScheduleDetailPage: React.FC = () => {
  const { scheduleId } = useParams<{ scheduleId: string }>();
  const [schedule, setSchedule] = useState<Schedule | null>(null);
  const [timeSlots, setTimeSlots] = useState<TimeSlot[]>([]);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [classGroups, setClassGroups] = useState<ClassGroup[]>([]);
  const [studyGroups, setStudyGroups] = useState<StudyGroup[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [selectedEntry, setSelectedEntry] = useState<ScheduleEntry | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (scheduleId) {
      loadSchedule();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scheduleId]);

  const loadSchedule = async () => {
    if (!scheduleId) return;
    try {
      setLoading(true);
      const data = await schedulesApi.getWithReferences(scheduleId);
      setSchedule(data.schedule);
      setTimeSlots(data.time_slots);
      setLessons(data.lessons);
      setTeachers(data.teachers);
      setRooms(data.rooms);
      setClassGroups(data.class_groups);
      setStudyGroups(data.study_groups);
      setStudents(data.students);
    } catch (error) {
      console.error("Failed to load schedule:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!scheduleId) return;
    if (!confirm("Это создаст новое расписание. Продолжить?")) {
      return;
    }
    try {
      setGenerating(true);
      const request: ScheduleGenerateRequest = { timeout: 300 };
      const result = await schedulesApi.generate(scheduleId, request);
      if (result.success) {
        await loadSchedule();
        alert(
          `Расписание успешно создано! Создано ${result.entries_count} записей.`,
        );
      } else {
        alert(`Создание не удалось: ${result.message}`);
      }
    } catch (error) {
      console.error("Failed to generate schedule:", error);
      alert(
        "Не удалось создать расписание. Пожалуйста, проверьте, что у вас настроены уроки, преподаватели, классы, аудитории и временные слоты.",
      );
    } finally {
      setGenerating(false);
    }
  };

  const handleExportPdf = async () => {
    if (!scheduleId) return;
    try {
      const result = await schedulesApi.exportPdf(scheduleId);
      // Открыть предварительно подписанный URL в новой вкладке для загрузки
      const a = document.createElement("a");
      a.href = result.url;
      a.download = result.filename;
      a.target = "_blank";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch (error) {
      console.error("Failed to export PDF:", error);
      alert("Не удалось экспортировать PDF");
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case "draft":
        return "bg-gray-100 text-gray-800";
      case "generated":
        return "bg-green-100 text-green-800";
      case "active":
        return "bg-blue-100 text-blue-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  if (loading) {
    return <div className="p-8">Загрузка...</div>;
  }

  if (!schedule) {
    return (
      <div className="p-8">
        <Card className="p-12 text-center">
          <Calendar className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">Расписание не найдено</p>
        </Card>
      </div>
    );
  }

  const days = [
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье",
  ];

  const timeSlotMap = new Map(timeSlots.map((ts) => [ts.id, ts]));
  const lessonMap = new Map(lessons.map((l) => [l.id, l]));
  const teacherMap = new Map(teachers.map((t) => [t.id, t]));
  const roomMap = new Map(rooms.map((r) => [r.id, r]));
  const classGroupMap = new Map(classGroups.map((cg) => [cg.id, cg]));
  const studyGroupMap = new Map(studyGroups.map((sg) => [sg.id, sg]));

  return (
    <div className="p-8">
      <div className="mb-6">
        <Button variant="outline" asChild>
          <Link to="/schedules">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Назад к расписаниям
          </Link>
        </Button>
      </div>

      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">{schedule.name}</h1>
          {schedule.academic_period && (
            <p className="text-muted-foreground">{schedule.academic_period}</p>
          )}
        </div>
        <div className="flex gap-2">
          {schedule.status === "draft" && (
            <Button onClick={handleGenerate} disabled={generating}>
              <RefreshCw
                className={`mr-2 h-4 w-4 ${generating ? "animate-spin" : ""}`}
              />
              {generating ? "Создание..." : "Создать расписание"}
            </Button>
          )}
          {schedule.status === "generated" && (
            <Button onClick={handleExportPdf}>
              <Download className="mr-2 h-4 w-4" />
              Экспорт PDF
            </Button>
          )}
        </div>
      </div>

      <Card className="p-6 mb-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-muted-foreground">Статус</p>
            <span
              className={`inline-block px-2 py-1 rounded text-sm font-semibold mt-1 ${getStatusBadgeColor(schedule.status)}`}
            >
              {schedule.status.charAt(0).toUpperCase() +
                schedule.status.slice(1)}
            </span>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Записей</p>
            <p className="font-semibold text-lg">{schedule.entries.length}</p>
          </div>
          {schedule.generated_at && (
            <div>
              <p className="text-sm text-muted-foreground">Создано</p>
              <p className="font-semibold text-sm">
                {new Date(schedule.generated_at).toLocaleDateString()}
              </p>
            </div>
          )}
          <div>
            <p className="text-sm text-muted-foreground">Создано</p>
            <p className="font-semibold text-sm">
              {new Date(schedule.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>
      </Card>

      {schedule.entries.length > 0 ? (
        <div className="space-y-6">
          <h2 className="text-xl font-semibold">Записи расписания</h2>

          {/* Группировать записи по дням */}
          {days.map((day, dayIndex) => {
            // Фильтровать записи по дню недели (0 = Понедельник, 6 = Воскресенье)
            let dayEntries = schedule.entries.filter((entry) => {
              const timeSlot = timeSlotMap.get(entry.time_slot_id);
              return timeSlot && timeSlot.day_of_week === dayIndex;
            });

            // Сортировать записи по времени начала
            dayEntries = dayEntries.sort((a, b) => {
              const timeSlotA = timeSlotMap.get(a.time_slot_id);
              const timeSlotB = timeSlotMap.get(b.time_slot_id);
              if (!timeSlotA || !timeSlotB) return 0;
              return timeSlotA.start_time.localeCompare(timeSlotB.start_time);
            });

            if (dayEntries.length === 0) return null;

            return (
              <Card key={day} className="p-6">
                <h3 className="text-lg font-semibold mb-4">{day}</h3>
                <div className="space-y-3">
                  {dayEntries.map((entry) => {
                    const timeSlot = timeSlotMap.get(entry.time_slot_id);
                    const timeStr = timeSlot
                      ? `${timeSlot.start_time.slice(0, 5)} - ${timeSlot.end_time.slice(0, 5)}`
                      : "—";
                    const lesson = lessonMap.get(entry.lesson_id);
                    const teacher = teacherMap.get(entry.teacher_id);
                    const room = roomMap.get(entry.room_id);
                    const groupName = entry.class_group_id
                      ? classGroupMap.get(entry.class_group_id)?.name
                      : entry.study_group_id
                        ? studyGroupMap.get(entry.study_group_id)?.name
                        : null;

                    return (
                      <div
                        key={entry.id}
                        role="button"
                        tabIndex={0}
                        onClick={() => setSelectedEntry(entry)}
                        onKeyDown={(e) =>
                          e.key === "Enter" && setSelectedEntry(entry)
                        }
                        className="border rounded-lg p-4 hover:bg-muted/50 transition-colors cursor-pointer"
                      >
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                          <div className="flex items-center gap-2">
                            <Clock className="h-4 w-4 text-muted-foreground" />
                            <div>
                              <p className="text-sm text-muted-foreground">
                                Время
                              </p>
                              <p className="font-medium">{timeStr}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <BookOpen className="h-4 w-4 text-muted-foreground" />
                            <div>
                              <p className="text-sm text-muted-foreground">
                                Урок
                              </p>
                              <p className="font-medium">{lesson?.name ?? "—"}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Users className="h-4 w-4 text-muted-foreground" />
                            <div>
                              <p className="text-sm text-muted-foreground">
                                {entry.class_group_id
                                  ? "Группа класса"
                                  : entry.study_group_id
                                    ? "Учебная группа"
                                    : "Группа"}
                              </p>
                              <p className="font-medium">{groupName ?? "—"}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <MapPin className="h-4 w-4 text-muted-foreground" />
                            <div>
                              <p className="text-sm text-muted-foreground">
                                Аудитория
                              </p>
                              <p className="font-medium">{room?.name ?? "—"}</p>
                            </div>
                          </div>
                        </div>
                        <div className="mt-2 pt-2 border-t">
                          <p className="text-sm text-muted-foreground">
                            Преподаватель: {teacher?.full_name ?? "—"}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </Card>
            );
          })}
        </div>
      ) : (
        <Card className="p-12 text-center">
          <Calendar className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground mb-4">Нет записей в расписании</p>
          {schedule.status === "draft" && (
            <Button onClick={handleGenerate} disabled={generating}>
              <RefreshCw
                className={`mr-2 h-4 w-4 ${generating ? "animate-spin" : ""}`}
              />
              {generating ? "Создание..." : "Создать расписание"}
            </Button>
          )}
        </Card>
      )}

      <Dialog open={!!selectedEntry} onOpenChange={(o) => !o && setSelectedEntry(null)}>
        <DialogContent className="max-w-lg">
          {selectedEntry && (() => {
            const ts = timeSlotMap.get(selectedEntry.time_slot_id);
            const les = lessonMap.get(selectedEntry.lesson_id);
            const tch = teacherMap.get(selectedEntry.teacher_id);
            const rm = roomMap.get(selectedEntry.room_id);
            const dayName = ts != null ? days[ts.day_of_week] : null;
            const timeStr = ts
              ? `${ts.start_time.slice(0, 5)} – ${ts.end_time.slice(0, 5)}`
              : "—";
            const isClass = !!selectedEntry.class_group_id;
            const cg = selectedEntry.class_group_id
              ? classGroupMap.get(selectedEntry.class_group_id)
              : null;
            const sg = selectedEntry.study_group_id
              ? studyGroupMap.get(selectedEntry.study_group_id)
              : null;
            const groupStudents = isClass
              ? students.filter((s) => s.class_group_id === selectedEntry.class_group_id)
              : sg?.students ?? [];

            return (
              <>
                <DialogHeader>
                  <DialogTitle>{les?.name ?? "Урок"}</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 text-sm">
                  <div className="flex items-start gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground mt-0.5" />
                    <div>
                      <p className="text-muted-foreground">Время</p>
                      <p className="font-medium">
                        {dayName && `${dayName}, `}{timeStr}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <BookOpen className="h-4 w-4 text-muted-foreground mt-0.5" />
                    <div>
                      <p className="text-muted-foreground">Урок</p>
                      <p className="font-medium">{les?.name ?? "—"}</p>
                      {(les?.subject_code || les?.duration_minutes) && (
                        <p className="text-muted-foreground text-xs mt-0.5">
                          {[
                            les?.subject_code,
                            les?.duration_minutes && `${les.duration_minutes} мин`,
                          ]
                            .filter(Boolean)
                            .join(" · ")}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <Users className="h-4 w-4 text-muted-foreground mt-0.5" />
                    <div>
                      <p className="text-muted-foreground">Преподаватель</p>
                      <p className="font-medium">{tch?.full_name ?? "—"}</p>
                      {tch?.subject && (
                        <p className="text-muted-foreground text-xs">{tch.subject}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <MapPin className="h-4 w-4 text-muted-foreground mt-0.5" />
                    <div>
                      <p className="text-muted-foreground">Аудитория</p>
                      <p className="font-medium">{rm?.name ?? "—"}</p>
                      {(rm?.capacity != null || rm?.room_type) && (
                        <p className="text-muted-foreground text-xs">
                          {[rm?.room_type, rm?.capacity != null && `вместимость ${rm.capacity}`]
                            .filter(Boolean)
                            .join(" · ")}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <Users className="h-4 w-4 text-muted-foreground mt-0.5" />
                    <div className="flex-1">
                      <p className="text-muted-foreground">
                        {isClass ? "Группа класса" : "Учебная группа"}
                      </p>
                      <p className="font-medium">
                        {isClass ? cg?.name ?? "—" : sg?.name ?? "—"}
                      </p>
                      {isClass && cg != null && (
                        <p className="text-muted-foreground text-xs">
                          Учеников: {cg.student_count}
                        </p>
                      )}
                      <p className="text-muted-foreground text-xs mt-2">Состав группы:</p>
                      {groupStudents.length > 0 ? (
                        <ul className="mt-1 space-y-0.5 text-xs max-h-32 overflow-y-auto">
                          {groupStudents.map((s, i) => {
                            const snap = s as { id?: string; full_name: string; student_number?: string | null };
                            return (
                              <li key={snap.id ?? `student-${i}`}>
                                {snap.full_name}
                                {snap.student_number && (
                                  <span className="text-muted-foreground ml-1">
                                    ({snap.student_number})
                                  </span>
                                )}
                              </li>
                            );
                          })}
                        </ul>
                      ) : (
                        <p className="text-muted-foreground text-xs mt-1">Нет данных</p>
                      )}
                    </div>
                  </div>
                </div>
              </>
            );
          })()}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ScheduleDetailPage;
