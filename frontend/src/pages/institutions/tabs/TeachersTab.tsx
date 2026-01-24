import React, { useEffect, useState } from "react";
import { Plus, Edit, Trash2, Users, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { teachersApi } from "@/api/teachers";
import { lessonsApi } from "@/api/lessons";
import type { Teacher } from "@/api/teachers";
import type { Lesson } from "@/api/lessons";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import axios from "axios";

const teacherSchema = z.object({
  full_name: z.string().min(1, "Полное имя обязательно"),
  subject: z.string().optional(),
});

type TeacherFormValues = z.infer<typeof teacherSchema>;

interface TeachersTabProps {
  institutionId: string;
}

export const TeachersTab: React.FC<TeachersTabProps> = ({ institutionId }) => {
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingTeacher, setEditingTeacher] = useState<Teacher | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [assigningTeacher, setAssigningTeacher] = useState<Teacher | null>(
    null,
  );
  const [isAssignDialogOpen, setIsAssignDialogOpen] = useState(false);
  const [teacherLessons, setTeacherLessons] = useState<
    Record<number, string[]>
  >({});

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [institutionId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [teachersData, lessonsData] = await Promise.all([
        teachersApi.list(institutionId),
        lessonsApi.list(institutionId),
      ]);
      setTeachers(teachersData);
      setLessons(lessonsData);

      // Загрузить назначения преподаватель-урок
      const assignments: Record<number, string[]> = {};
      const assignmentPromises = teachersData.map(async (teacher) => {
        try {
          const assignmentsData = await teachersApi.getLessons(teacher.id);
          assignments[teacher.id] = assignmentsData.map((a) => a.lesson_id);
        } catch (error) {
          console.error(
            `Failed to load lessons for teacher ${teacher.id}:`,
            error,
          );
          assignments[teacher.id] = [];
        }
      });
      await Promise.all(assignmentPromises);
      setTeacherLessons(assignments);
    } catch (error) {
      console.error("Failed to load data:", error);
    } finally {
      setLoading(false);
    }
  };

  const form = useForm<TeacherFormValues>({
    resolver: zodResolver(teacherSchema),
    defaultValues: {
      full_name: "",
      subject: "",
    },
  });

  useEffect(() => {
    if (editingTeacher) {
      form.reset({
        full_name: editingTeacher.full_name,
        subject: editingTeacher.subject || "",
      });
    } else {
      form.reset({
        full_name: "",
        subject: "",
      });
    }
  }, [editingTeacher, form]);

  const onSubmit = async (data: TeacherFormValues) => {
    try {
      if (editingTeacher) {
        await teachersApi.update(editingTeacher.id, data);
      } else {
        await teachersApi.create(institutionId, data);
      }
      setIsDialogOpen(false);
      setEditingTeacher(null);
      await loadData();
    } catch (error) {
      console.error("Failed to save teacher:", error);
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        alert(error.response.data.detail);
      } else {
        alert("Не удалось сохранить преподавателя");
      }
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Вы уверены, что хотите удалить этого преподавателя?")) return;
    try {
      await teachersApi.delete(id);
      await loadData();
    } catch (error) {
      console.error("Failed to delete teacher:", error);
      alert("Не удалось удалить преподавателя");
    }
  };

  const handleEdit = (teacher: Teacher) => {
    setEditingTeacher(teacher);
    setIsDialogOpen(true);
  };

  const handleNew = () => {
    setEditingTeacher(null);
    setIsDialogOpen(true);
  };

  const handleAssignLessons = async (selectedLessonIds: string[]) => {
    if (!assigningTeacher) return;
    try {
      await teachersApi.assignLessons(assigningTeacher.id, selectedLessonIds);
      setIsAssignDialogOpen(false);
      setAssigningTeacher(null);
      await loadData();
    } catch (error) {
      console.error("Failed to assign lessons:", error);
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        alert(error.response.data.detail);
      } else {
        alert("Не удалось назначить уроки");
      }
    }
  };

  if (loading) {
    return <div className="p-4">Загрузка преподавателей...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Преподаватели</h3>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={handleNew}>
              <Plus className="mr-2 h-4 w-4" />
              Новый преподаватель
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {editingTeacher ? "Редактировать преподавателя" : "Создать преподавателя"}
              </DialogTitle>
            </DialogHeader>
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="space-y-4"
              >
                <FormField
                  control={form.control}
                  name="full_name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Полное имя</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="subject"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Предмет</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <div className="flex justify-end gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setIsDialogOpen(false);
                      setEditingTeacher(null);
                    }}
                  >
                    Отмена
                  </Button>
                  <Button type="submit">
                    {editingTeacher ? "Обновить" : "Создать"}
                  </Button>
                </div>
              </form>
            </Form>
          </DialogContent>
        </Dialog>
      </div>

      {teachers.length === 0 ? (
        <Card className="p-8 text-center">
          <Users className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">
            Пока нет преподавателей. Создайте первого преподавателя.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {teachers.map((teacher) => (
            <Card key={teacher.id} className="p-4">
              <div className="flex justify-between items-start mb-2">
                <div className="flex-1">
                  <h4 className="font-semibold">{teacher.full_name}</h4>
                  {teacher.subject && (
                    <p className="text-sm text-muted-foreground">
                      {teacher.subject}
                    </p>
                  )}
                  <div className="mt-2">
                    <p className="text-xs text-muted-foreground mb-1">
                      Назначенные уроки:
                    </p>
                    {teacherLessons[teacher.id]?.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {teacherLessons[teacher.id].map((lessonId) => {
                          const lesson = lessons.find((l) => l.id === lessonId);
                          return lesson ? (
                            <span
                              key={lessonId}
                              className="inline-flex items-center gap-1 px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded"
                            >
                              <BookOpen className="h-3 w-3" />
                              {lesson.name}
                            </span>
                          ) : null;
                        })}
                      </div>
                    ) : (
                      <p className="text-xs text-muted-foreground">
                        Нет назначенных уроков
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleEdit(teacher)}
                    title="Редактировать"
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => {
                      setAssigningTeacher(teacher);
                      setIsAssignDialogOpen(true);
                    }}
                    title="Назначить уроки"
                  >
                    <BookOpen className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(teacher.id)}
                    title="Удалить"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Assign Lessons Dialog */}
      <Dialog open={isAssignDialogOpen} onOpenChange={setIsAssignDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              Назначить уроки для {assigningTeacher?.full_name}
            </DialogTitle>
          </DialogHeader>
          <AssignLessonsForm
            lessons={lessons}
            selectedLessonIds={
              assigningTeacher ? teacherLessons[assigningTeacher.id] || [] : []
            }
            onAssign={handleAssignLessons}
            onCancel={() => {
              setIsAssignDialogOpen(false);
              setAssigningTeacher(null);
            }}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
};

interface AssignLessonsFormProps {
  lessons: Lesson[];
  selectedLessonIds: string[];
  onAssign: (lessonIds: string[]) => void;
  onCancel: () => void;
}

const AssignLessonsForm: React.FC<AssignLessonsFormProps> = ({
  lessons,
  selectedLessonIds,
  onAssign,
  onCancel,
}) => {
  const [selected, setSelected] = useState<Set<string>>(
    new Set(selectedLessonIds),
  );

  useEffect(() => {
    setSelected(new Set(selectedLessonIds));
  }, [selectedLessonIds]);

  const handleToggle = (lessonId: string) => {
    const newSelected = new Set(selected);
    if (newSelected.has(lessonId)) {
      newSelected.delete(lessonId);
    } else {
      newSelected.add(lessonId);
    }
    setSelected(newSelected);
  };

  const handleSubmit = () => {
    onAssign(Array.from(selected));
  };

  return (
    <div className="space-y-4">
      <div className="max-h-60 overflow-y-auto space-y-2">
        {lessons.length === 0 ? (
          <p className="text-sm text-muted-foreground">Нет доступных уроков</p>
        ) : (
          lessons.map((lesson) => (
            <label
              key={lesson.id}
              className="flex items-center space-x-2 p-2 rounded hover:bg-accent cursor-pointer"
            >
              <input
                type="checkbox"
                checked={selected.has(lesson.id)}
                onChange={() => handleToggle(lesson.id)}
                className="rounded"
              />
              <div>
                <span className="text-sm font-medium">{lesson.name}</span>
                {lesson.subject_code && (
                  <span className="text-xs text-muted-foreground ml-2">
                    ({lesson.subject_code})
                  </span>
                )}
                <span className="text-xs text-muted-foreground ml-2">
                  {lesson.duration_minutes} min
                </span>
              </div>
            </label>
          ))
        )}
      </div>
      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={onCancel}>
          Отмена
        </Button>
        <Button onClick={handleSubmit}>Назначить</Button>
      </div>
    </div>
  );
};

export default TeachersTab;
