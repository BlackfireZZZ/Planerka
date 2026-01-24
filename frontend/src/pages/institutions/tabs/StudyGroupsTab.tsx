import React, { useEffect, useState } from "react";
import { Plus, Edit, Trash2, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { studyGroupsApi } from "@/api/studyGroups";
import { streamsApi } from "@/api/streams";
import { studentsApi } from "@/api/students";
import type { StudyGroup } from "@/api/studyGroups";
import type { Stream } from "@/api/streams";
import type { Student } from "@/api/students";
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
import { Checkbox } from "@/components/ui/checkbox";
import axios from "axios";

const studyGroupSchema = z.object({
  stream_id: z.string().min(1, "Поток обязателен"),
  name: z.string().min(1, "Название обязательно"),
  student_ids: z.array(z.string()),
});

interface StudyGroupsTabProps {
  institutionId: string;
}

export const StudyGroupsTab: React.FC<StudyGroupsTabProps> = ({
  institutionId,
}) => {
  const [studyGroups, setStudyGroups] = useState<StudyGroup[]>([]);
  const [streams, setStreams] = useState<Stream[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingStudyGroup, setEditingStudyGroup] =
    useState<StudyGroup | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [institutionId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [streamsData, studyGroupsData, studentsData] = await Promise.all([
        streamsApi.list(institutionId),
        studyGroupsApi.list(institutionId),
        studentsApi.list(institutionId),
      ]);
      setStreams(streamsData);
      setStudyGroups(studyGroupsData);
      setStudents(studentsData);
    } catch (error) {
      console.error("Failed to load data:", error);
    } finally {
      setLoading(false);
    }
  };

  const form = useForm({
    resolver: zodResolver(studyGroupSchema),
    defaultValues: {
      stream_id: "",
      name: "",
      student_ids: [] as string[],
    },
  });

  const selectedStream = form.watch("stream_id");

  // Получить студентов из групп классов в выбранном потоке
  const getAvailableStudents = () => {
    if (!selectedStream) return [];
    const stream = streams.find((s) => s.id === selectedStream);
    if (!stream) return [];
    const streamClassGroupIds = new Set(
      stream.class_groups.map((cg) => cg.id),
    );
    return students.filter((s) => streamClassGroupIds.has(s.class_group_id));
  };

  useEffect(() => {
    if (editingStudyGroup) {
      form.reset({
        stream_id: editingStudyGroup.stream_id,
        name: editingStudyGroup.name,
        student_ids: editingStudyGroup.students.map((s) => s.id),
      });
    } else {
      form.reset({
        stream_id: "",
        name: "",
        student_ids: [],
      });
    }
  }, [editingStudyGroup, form]);

  const onSubmit = async (data: z.infer<typeof studyGroupSchema>) => {
    try {
      if (editingStudyGroup) {
        await studyGroupsApi.update(editingStudyGroup.id, data);
      } else {
        await studyGroupsApi.create(institutionId, data);
      }
      setIsDialogOpen(false);
      setEditingStudyGroup(null);
      await loadData();
    } catch (error) {
      console.error("Failed to save study group:", error);
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        alert(error.response.data.detail);
      } else {
        alert("Не удалось сохранить учебную группу");
      }
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Вы уверены, что хотите удалить эту учебную группу?")) return;
    try {
      await studyGroupsApi.delete(id);
      await loadData();
    } catch (error) {
      console.error("Failed to delete study group:", error);
      alert("Не удалось удалить учебную группу");
    }
  };

  const handleEdit = (studyGroup: StudyGroup) => {
    setEditingStudyGroup(studyGroup);
    setIsDialogOpen(true);
  };

  const handleNew = () => {
    setEditingStudyGroup(null);
    setIsDialogOpen(true);
  };

  const getStreamName = (streamId: string) => {
    return streams.find((s) => s.id === streamId)?.name || "Неизвестно";
  };

  if (loading) {
    return <div className="p-4">Загрузка учебных групп...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Учебные группы</h3>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={handleNew} disabled={streams.length === 0}>
              <Plus className="mr-2 h-4 w-4" />
              Новая учебная группа
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {editingStudyGroup
                  ? "Редактировать учебную группу"
                  : "Создать учебную группу"}
              </DialogTitle>
            </DialogHeader>
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="space-y-4"
              >
                <FormField
                  control={form.control}
                  name="stream_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Поток</FormLabel>
                      <FormControl>
                        <select
                          {...field}
                          className="w-full px-3 py-2 border rounded-md"
                          onChange={(e) => {
                            field.onChange(e.target.value);
                            // Очистить выбор студентов при изменении потока
                            form.setValue("student_ids", []);
                          }}
                        >
                          <option value="">Выберите поток</option>
                          {streams.map((stream) => (
                            <option key={stream.id} value={stream.id}>
                              {stream.name}
                            </option>
                          ))}
                        </select>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
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
                  name="student_ids"
                  render={() => (
                    <FormItem>
                      <div className="mb-4">
                        <FormLabel>Студенты</FormLabel>
                        <p className="text-sm text-muted-foreground">
                          {selectedStream
                            ? "Выберите студентов из групп классов в этом потоке"
                            : "Сначала выберите поток, чтобы увидеть доступных студентов"}
                        </p>
                      </div>
                      {selectedStream ? (
                        getAvailableStudents().length > 0 ? (
                          getAvailableStudents().map((student) => (
                            <FormField
                              key={student.id}
                              control={form.control}
                              name="student_ids"
                              render={({ field }) => {
                                return (
                                  <FormItem
                                    key={student.id}
                                    className="flex flex-row items-start space-x-3 space-y-0"
                                  >
                                    <FormControl>
                                      <Checkbox
                                        checked={field.value?.includes(
                                          student.id,
                                        )}
                                        onCheckedChange={(checked: boolean) => {
                                          return checked
                                            ? field.onChange([
                                                ...field.value,
                                                student.id,
                                              ])
                                            : field.onChange(
                                                field.value?.filter(
                                                  (value) =>
                                                    value !== student.id,
                                                ),
                                              );
                                        }}
                                      />
                                    </FormControl>
                                    <FormLabel className="font-normal">
                                      {student.full_name}
                                      {student.student_number &&
                                        ` (${student.student_number})`}
                                    </FormLabel>
                                  </FormItem>
                                );
                              }}
                            />
                          ))
                        ) : (
                          <p className="text-sm text-muted-foreground">
                            Нет доступных студентов в группах классов этого потока
                          </p>
                        )
                      ) : null}
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
                      setEditingStudyGroup(null);
                    }}
                  >
                    Отмена
                  </Button>
                  <Button type="submit">
                    {editingStudyGroup ? "Обновить" : "Создать"}
                  </Button>
                </div>
              </form>
            </Form>
          </DialogContent>
        </Dialog>
      </div>

      {studyGroups.length === 0 ? (
        <Card className="p-8 text-center">
          <Users className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">
            Пока нет учебных групп. Создайте первую учебную группу.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {studyGroups.map((studyGroup) => (
            <Card key={studyGroup.id} className="p-4">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="font-semibold">{studyGroup.name}</h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    Поток: {getStreamName(studyGroup.stream_id)}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {studyGroup.students.length} студент{studyGroup.students.length !== 1 ? "ов" : ""}
                  </p>
                  {studyGroup.students.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs text-muted-foreground">
                        {studyGroup.students
                          .map((s) => s.full_name)
                          .slice(0, 3)
                          .join(", ")}
                        {studyGroup.students.length > 3 && "..."}
                      </p>
                    </div>
                  )}
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleEdit(studyGroup)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(studyGroup.id)}
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

export default StudyGroupsTab;
