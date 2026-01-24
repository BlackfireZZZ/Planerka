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
import { schedulesApi } from "@/api/schedules";
import { timeSlotsApi } from "@/api/timeSlots";
import type { Schedule, ScheduleGenerateRequest } from "@/api/schedules";
import type { TimeSlot } from "@/api/timeSlots";

export const ScheduleDetailPage: React.FC = () => {
  const { scheduleId } = useParams<{ scheduleId: string }>();
  const [schedule, setSchedule] = useState<Schedule | null>(null);
  const [timeSlots, setTimeSlots] = useState<TimeSlot[]>([]);
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
      const data = await schedulesApi.get(scheduleId);
      setSchedule(data);

      // Загрузить временные слоты для фильтрации по дню недели
      if (data.institution_id) {
        try {
          const slots = await timeSlotsApi.list(data.institution_id);
          setTimeSlots(slots);
        } catch (error) {
          console.error("Failed to load time slots:", error);
        }
      }
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

  // Создать карту time_slot_id -> time_slot для быстрого поиска
  const timeSlotMap = new Map(timeSlots.map((ts) => [ts.id, ts]));

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
                      : entry.time_slot_id.slice(0, 8) + "...";

                    return (
                      <div
                        key={entry.id}
                        className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
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
                              <p className="font-medium">
                                {entry.lesson_id.slice(0, 8)}...
                              </p>
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
                              <p className="font-medium">
                                {entry.class_group_id
                                  ? `${entry.class_group_id.slice(0, 8)}...`
                                  : entry.study_group_id
                                    ? `${entry.study_group_id.slice(0, 8)}... (Учебная)`
                                    : "Н/Д"}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <MapPin className="h-4 w-4 text-muted-foreground" />
                            <div>
                              <p className="text-sm text-muted-foreground">
                                Аудитория
                              </p>
                              <p className="font-medium">
                                {entry.room_id.slice(0, 8)}...
                              </p>
                            </div>
                          </div>
                        </div>
                        <div className="mt-2 pt-2 border-t">
                          <p className="text-xs text-muted-foreground">
                            ID преподавателя: {entry.teacher_id}
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
    </div>
  );
};

export default ScheduleDetailPage;
