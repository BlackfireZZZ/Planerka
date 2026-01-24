import React, { useEffect, useState } from "react";
import { Plus, Edit, Trash2, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { classGroupsApi } from "@/api/classGroups";
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

const classGroupSchema = z.object({
  name: z.string().min(1, "Название обязательно"),
  student_count: z.number().min(0),
});

type ClassGroupFormValues = z.infer<typeof classGroupSchema>;

interface ClassGroupsTabProps {
  institutionId: string;
}

export const ClassGroupsTab: React.FC<ClassGroupsTabProps> = ({
  institutionId,
}) => {
  const [classGroups, setClassGroups] = useState<ClassGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingClassGroup, setEditingClassGroup] = useState<ClassGroup | null>(
    null,
  );
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  useEffect(() => {
    loadClassGroups();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [institutionId]);

  const loadClassGroups = async () => {
    try {
      setLoading(true);
      const data = await classGroupsApi.list(institutionId);
      setClassGroups(data);
    } catch (error) {
      console.error("Failed to load class groups:", error);
    } finally {
      setLoading(false);
    }
  };

  const form = useForm<ClassGroupFormValues>({
    resolver: zodResolver(classGroupSchema),
    defaultValues: {
      name: "",
      student_count: 0,
    },
  });

  useEffect(() => {
    if (editingClassGroup) {
      form.reset({
        name: editingClassGroup.name,
        student_count: editingClassGroup.student_count,
      });
    } else {
      form.reset({
        name: "",
        student_count: 0,
      });
    }
  }, [editingClassGroup, form]);

  const onSubmit = async (data: ClassGroupFormValues) => {
    try {
      if (editingClassGroup) {
        await classGroupsApi.update(editingClassGroup.id, data);
      } else {
        await classGroupsApi.create(institutionId, data);
      }
      setIsDialogOpen(false);
      setEditingClassGroup(null);
      await loadClassGroups();
    } catch (error) {
      console.error("Failed to save class group:", error);
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        alert(error.response.data.detail);
      } else {
        alert("Не удалось сохранить группу класса");
      }
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Вы уверены, что хотите удалить эту группу класса?")) return;
    try {
      await classGroupsApi.delete(id);
      await loadClassGroups();
    } catch (error) {
      console.error("Failed to delete class group:", error);
      alert("Не удалось удалить группу класса");
    }
  };

  const handleEdit = (classGroup: ClassGroup) => {
    setEditingClassGroup(classGroup);
    setIsDialogOpen(true);
  };

  const handleNew = () => {
    setEditingClassGroup(null);
    setIsDialogOpen(true);
  };

  if (loading) {
    return <div className="p-4">Загрузка групп классов...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Группы классов</h3>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={handleNew}>
              <Plus className="mr-2 h-4 w-4" />
              Новая группа класса
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {editingClassGroup ? "Редактировать группу класса" : "Создать группу класса"}
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
                  name="student_count"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Количество студентов</FormLabel>
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
                      setEditingClassGroup(null);
                    }}
                  >
                    Отмена
                  </Button>
                  <Button type="submit">
                    {editingClassGroup ? "Обновить" : "Создать"}
                  </Button>
                </div>
              </form>
            </Form>
          </DialogContent>
        </Dialog>
      </div>

      {classGroups.length === 0 ? (
        <Card className="p-8 text-center">
          <Users className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">
            Пока нет групп классов. Создайте первую группу класса.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {classGroups.map((classGroup) => (
            <Card key={classGroup.id} className="p-4">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="font-semibold">{classGroup.name}</h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    Студентов: {classGroup.student_count}
                  </p>
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleEdit(classGroup)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(classGroup.id)}
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

export default ClassGroupsTab;
