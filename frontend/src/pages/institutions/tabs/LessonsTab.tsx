import React, { useEffect, useState } from "react";
import { Plus, Edit, Trash2, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { lessonsApi } from "@/api/lessons";
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

const lessonSchema = z.object({
  name: z.string().min(1, "Название обязательно"),
  subject_code: z.string().optional(),
  duration_minutes: z.number().min(1).max(480),
});

type LessonFormValues = z.infer<typeof lessonSchema>;

interface LessonsTabProps {
  institutionId: string;
}

export const LessonsTab: React.FC<LessonsTabProps> = ({ institutionId }) => {
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingLesson, setEditingLesson] = useState<Lesson | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  useEffect(() => {
    loadLessons();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [institutionId]);

  const loadLessons = async () => {
    try {
      setLoading(true);
      const data = await lessonsApi.list(institutionId);
      setLessons(data);
    } catch (error) {
      console.error("Failed to load lessons:", error);
    } finally {
      setLoading(false);
    }
  };

  const form = useForm<LessonFormValues>({
    resolver: zodResolver(lessonSchema),
    defaultValues: {
      name: "",
      subject_code: "",
      duration_minutes: 90,
    },
  });

  useEffect(() => {
    if (editingLesson) {
      form.reset({
        name: editingLesson.name,
        subject_code: editingLesson.subject_code || "",
        duration_minutes: editingLesson.duration_minutes,
      });
    } else {
      form.reset({
        name: "",
        subject_code: "",
        duration_minutes: 90,
      });
    }
  }, [editingLesson, form]);

  const onSubmit = async (data: LessonFormValues) => {
    try {
      if (editingLesson) {
        await lessonsApi.update(editingLesson.id, data);
      } else {
        await lessonsApi.create(institutionId, data);
      }
      setIsDialogOpen(false);
      setEditingLesson(null);
      await loadLessons();
    } catch (error) {
      console.error("Failed to save lesson:", error);
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        alert(error.response.data.detail);
      } else {
        alert("Не удалось сохранить урок");
      }
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Вы уверены, что хотите удалить этот урок?")) return;
    try {
      await lessonsApi.delete(id);
      await loadLessons();
    } catch (error) {
      console.error("Failed to delete lesson:", error);
      alert("Не удалось удалить урок");
    }
  };

  const handleEdit = (lesson: Lesson) => {
    setEditingLesson(lesson);
    setIsDialogOpen(true);
  };

  const handleNew = () => {
    setEditingLesson(null);
    setIsDialogOpen(true);
  };

  if (loading) {
    return <div className="p-4">Загрузка уроков...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Уроки</h3>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={handleNew}>
              <Plus className="mr-2 h-4 w-4" />
              Новый урок
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {editingLesson ? "Редактировать урок" : "Создать урок"}
              </DialogTitle>
            </DialogHeader>
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="space-y-4"
              >
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Название</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="subject_code"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Код предмета</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="duration_minutes"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Длительность (минуты)</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          {...field}
                          onChange={(e) =>
                            field.onChange(parseInt(e.target.value) || 0)
                          }
                        />
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
                      setEditingLesson(null);
                    }}
                  >
                    Отмена
                  </Button>
                  <Button type="submit">
                    {editingLesson ? "Обновить" : "Создать"}
                  </Button>
                </div>
              </form>
            </Form>
          </DialogContent>
        </Dialog>
      </div>

      {lessons.length === 0 ? (
        <Card className="p-8 text-center">
          <BookOpen className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">
            Пока нет уроков. Создайте первый урок.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {lessons.map((lesson) => (
            <Card key={lesson.id} className="p-4">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="font-semibold">{lesson.name}</h4>
                  {lesson.subject_code && (
                    <p className="text-sm text-muted-foreground">
                      {lesson.subject_code}
                    </p>
                  )}
                  <p className="text-sm text-muted-foreground mt-1">
                    Длительность: {lesson.duration_minutes} мин
                  </p>
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleEdit(lesson)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(lesson.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default LessonsTab;
