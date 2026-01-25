import React, { useEffect, useState } from "react";
import { Plus, Edit, Trash2, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { studentsApi } from "@/api/students";
import { classGroupsApi } from "@/api/classGroups";
import type { Student } from "@/api/students";
import type { ClassGroup } from "@/api/classGroups";
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

const studentSchema = z.object({
  class_group_id: z.string().min(1, "Группа класса обязательна"),
  full_name: z.string().min(1, "Полное имя обязательно"),
  student_number: z.string().optional(),
});

type StudentFormValues = z.infer<typeof studentSchema>;

interface StudentsTabProps {
  institutionId: string;
}

export const StudentsTab: React.FC<StudentsTabProps> = ({ institutionId }) => {
  const [students, setStudents] = useState<Student[]>([]);
  const [classGroups, setClassGroups] = useState<ClassGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingStudent, setEditingStudent] = useState<Student | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [institutionId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [studentsData, classGroupsData] = await Promise.all([
        studentsApi.list(institutionId),
        classGroupsApi.list(institutionId),
      ]);
      setStudents(studentsData);
      setClassGroups(classGroupsData);
    } catch (error) {
      console.error("Failed to load data:", error);
    } finally {
      setLoading(false);
    }
  };

  const form = useForm<StudentFormValues>({
    resolver: zodResolver(studentSchema),
    defaultValues: {
      class_group_id: "",
      full_name: "",
      student_number: "",
    },
  });

  useEffect(() => {
    if (editingStudent) {
      form.reset({
        class_group_id: editingStudent.class_group_id,
        full_name: editingStudent.full_name,
        student_number: editingStudent.student_number || "",
      });
    } else {
      form.reset({
        class_group_id: classGroups[0]?.id || "",
        full_name: "",
        student_number: "",
      });
    }
  }, [editingStudent, classGroups, form]);

  const onSubmit = async (data: StudentFormValues) => {
    try {
      if (editingStudent) {
        await studentsApi.update(editingStudent.id, data);
      } else {
        await studentsApi.create(institutionId, data);
      }
      setIsDialogOpen(false);
      setEditingStudent(null);
      await loadData();
    } catch (error) {
      console.error("Failed to save student:", error);
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        alert(error.response.data.detail);
      } else {
        alert("Не удалось сохранить студента");
      }
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Вы уверены, что хотите удалить этого студента?")) return;
    try {
      await studentsApi.delete(id);
      await loadData();
    } catch (error) {
      console.error("Failed to delete student:", error);
      alert("Не удалось удалить студента");
    }
  };

  const handleEdit = (student: Student) => {
    setEditingStudent(student);
    setIsDialogOpen(true);
  };

  const handleNew = () => {
    setEditingStudent(null);
    setIsDialogOpen(true);
  };

  const getClassGroupName = (classGroupId: string) => {
    return (
      classGroups.find((cg) => cg.id === classGroupId)?.name || "Неизвестно"
    );
  };

  if (loading) {
    return <div className="p-4">Загрузка студентов...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Студенты</h3>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={handleNew} disabled={classGroups.length === 0}>
              <Plus className="mr-2 h-4 w-4" />
              Новый студент
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {editingStudent ? "Редактировать студента" : "Создать студента"}
              </DialogTitle>
            </DialogHeader>
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="space-y-4"
              >
                <FormField
                  control={form.control}
                  name="class_group_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Группа класса</FormLabel>
                      <FormControl>
                        <select
                          {...field}
                          className="w-full px-3 py-2 border rounded-md"
                        >
                          {classGroups.map((cg) => (
                            <option key={cg.id} value={cg.id}>
                              {cg.name}
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
                  name="student_number"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Номер студента</FormLabel>
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
                      setEditingStudent(null);
                    }}
                  >
                    Отмена
                  </Button>
                  <Button type="submit">
                    {editingStudent ? "Обновить" : "Создать"}
                  </Button>
                </div>
              </form>
            </Form>
          </DialogContent>
        </Dialog>
      </div>

      {students.length === 0 ? (
        <Card className="p-8 text-center">
          <Users className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">
            Пока нет студентов. Создайте первого студента.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {students.map((student) => (
            <Card key={student.id} className="p-4">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="font-semibold">{student.full_name}</h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    Класс: {getClassGroupName(student.class_group_id)}
                  </p>
                  {student.student_number && (
                    <p className="text-sm text-muted-foreground">
                      Номер: {student.student_number}
                    </p>
                  )}
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleEdit(student)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(student.id)}
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

export default StudentsTab;
