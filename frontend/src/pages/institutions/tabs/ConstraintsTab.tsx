import React, { useEffect, useState } from "react";
import { Plus, Edit, Trash2, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { constraintsApi } from "@/api/constraints";
import type { Constraint } from "@/api/constraints";
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
import { Textarea } from "@/components/ui/textarea";
import axios from "axios";

const constraintSchema = z.object({
  constraint_type: z.string().min(1, "Тип ограничения обязателен"),
  constraint_data: z.record(z.string(), z.unknown()),
  priority: z.number().min(0).max(10),
});

type ConstraintFormValues = z.infer<typeof constraintSchema>;

interface ConstraintsTabProps {
  institutionId: string;
}

export const ConstraintsTab: React.FC<ConstraintsTabProps> = ({
  institutionId,
}) => {
  const [constraints, setConstraints] = useState<Constraint[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingConstraint, setEditingConstraint] = useState<Constraint | null>(
    null,
  );
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [constraintDataJson, setConstraintDataJson] = useState("{}");

  useEffect(() => {
    loadConstraints();
  }, [institutionId]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadConstraints = async () => {
    try {
      setLoading(true);
      const data = await constraintsApi.list(institutionId);
      setConstraints(data);
    } catch (error) {
      console.error("Failed to load constraints:", error);
    } finally {
      setLoading(false);
    }
  };

  const form = useForm<ConstraintFormValues>({
    resolver: zodResolver(constraintSchema),
    defaultValues: {
      constraint_type: "",
      constraint_data: {} as Record<string, unknown>,
      priority: 5,
    },
  });

  useEffect(() => {
    if (editingConstraint) {
      form.reset({
        constraint_type: editingConstraint.constraint_type,
        constraint_data: editingConstraint.constraint_data,
        priority: editingConstraint.priority,
      });
      setConstraintDataJson(
        JSON.stringify(editingConstraint.constraint_data, null, 2),
      );
    } else {
      form.reset({
        constraint_type: "",
        constraint_data: {},
        priority: 5,
      });
      setConstraintDataJson("{}");
    }
  }, [editingConstraint, form]);

  const onSubmit = async (data: ConstraintFormValues) => {
    try {
      let constraintData = data.constraint_data;
      try {
        constraintData = JSON.parse(constraintDataJson) as Record<
          string,
          unknown
        >;
      } catch {
        alert("Неверный JSON в данных ограничения");
        return;
      }

      const submitData = {
        ...data,
        constraint_data: constraintData,
      };

      if (editingConstraint) {
        await constraintsApi.update(editingConstraint.id, submitData);
      } else {
        await constraintsApi.create(institutionId, submitData);
      }
      setIsDialogOpen(false);
      setEditingConstraint(null);
      await loadConstraints();
    } catch (error) {
      console.error("Failed to save constraint:", error);
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        alert(error.response.data.detail);
      } else {
        alert("Не удалось сохранить ограничение");
      }
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Вы уверены, что хотите удалить это ограничение?")) return;
    try {
      await constraintsApi.delete(id);
      await loadConstraints();
    } catch (error) {
      console.error("Failed to delete constraint:", error);
      alert("Не удалось удалить ограничение");
    }
  };

  const handleEdit = (constraint: Constraint) => {
    setEditingConstraint(constraint);
    setIsDialogOpen(true);
  };

  const handleNew = () => {
    setEditingConstraint(null);
    setIsDialogOpen(true);
  };

  if (loading) {
    return <div className="p-4">Загрузка ограничений...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Ограничения</h3>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={handleNew}>
              <Plus className="mr-2 h-4 w-4" />
              Новое ограничение
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {editingConstraint ? "Редактировать ограничение" : "Создать ограничение"}
              </DialogTitle>
            </DialogHeader>
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="space-y-4"
              >
                <FormField
                  control={form.control}
                  name="constraint_type"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Тип ограничения</FormLabel>
                      <FormControl>
                        <Input
                          {...field}
                          placeholder="например, доступность_преподавателя, вместимость_аудитории"
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="priority"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Приоритет (0-10)</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          {...field}
                          onChange={(e) =>
                            field.onChange(parseInt(e.target.value) || 5)
                          }
                          min={0}
                          max={10}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <div>
                  <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 mb-2 block">
                    Данные ограничения (JSON)
                  </label>
                  <Textarea
                    value={constraintDataJson}
                    onChange={(e) => setConstraintDataJson(e.target.value)}
                    className="font-mono text-sm"
                    rows={8}
                    placeholder='{"key": "value"}'
                  />
                </div>
                <div className="flex justify-end gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setIsDialogOpen(false);
                      setEditingConstraint(null);
                    }}
                  >
                    Отмена
                  </Button>
                  <Button type="submit">
                    {editingConstraint ? "Обновить" : "Создать"}
                  </Button>
                </div>
              </form>
            </Form>
          </DialogContent>
        </Dialog>
      </div>

      {constraints.length === 0 ? (
        <Card className="p-8 text-center">
          <AlertTriangle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">
            Пока нет ограничений. Создайте первое ограничение.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {constraints.map((constraint) => (
            <Card key={constraint.id} className="p-4">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="font-semibold">
                    {constraint.constraint_type}
                  </h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    Приоритет: {constraint.priority}
                  </p>
                  <pre className="text-xs text-muted-foreground mt-2 overflow-auto max-h-32">
                    {JSON.stringify(constraint.constraint_data, null, 2)}
                  </pre>
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleEdit(constraint)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(constraint.id)}
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

export default ConstraintsTab;
