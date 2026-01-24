import React, { useEffect, useState } from "react";
import { Plus, Edit, Trash2, Layers } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { streamsApi } from "@/api/streams";
import { classGroupsApi } from "@/api/classGroups";
import type { Stream } from "@/api/streams";
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
import { Checkbox } from "@/components/ui/checkbox";
import axios from "axios";

const streamSchema = z.object({
  name: z.string().min(1, "Название обязательно"),
  class_group_ids: z.array(z.string()),
});

interface StreamsTabProps {
  institutionId: string;
}

export const StreamsTab: React.FC<StreamsTabProps> = ({ institutionId }) => {
  const [streams, setStreams] = useState<Stream[]>([]);
  const [classGroups, setClassGroups] = useState<ClassGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingStream, setEditingStream] = useState<Stream | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [institutionId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [streamsData, classGroupsData] = await Promise.all([
        streamsApi.list(institutionId),
        classGroupsApi.list(institutionId),
      ]);
      setStreams(streamsData);
      setClassGroups(classGroupsData);
    } catch (error) {
      console.error("Failed to load data:", error);
    } finally {
      setLoading(false);
    }
  };

  const form = useForm({
    resolver: zodResolver(streamSchema),
    defaultValues: {
      name: "",
      class_group_ids: [] as string[],
    },
  });

  useEffect(() => {
    if (editingStream) {
      form.reset({
        name: editingStream.name,
        class_group_ids: editingStream.class_groups.map((cg) => cg.id),
      });
    } else {
      form.reset({
        name: "",
        class_group_ids: [],
      });
    }
  }, [editingStream, form]);

  const onSubmit = async (data: z.infer<typeof streamSchema>) => {
    try {
      if (editingStream) {
        await streamsApi.update(editingStream.id, data);
      } else {
        await streamsApi.create(institutionId, data);
      }
      setIsDialogOpen(false);
      setEditingStream(null);
      await loadData();
    } catch (error) {
      console.error("Failed to save stream:", error);
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        alert(error.response.data.detail);
      } else {
        alert("Не удалось сохранить поток");
      }
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Вы уверены, что хотите удалить этот поток?")) return;
    try {
      await streamsApi.delete(id);
      await loadData();
    } catch (error) {
      console.error("Failed to delete stream:", error);
      alert("Не удалось удалить поток");
    }
  };

  const handleEdit = (stream: Stream) => {
    setEditingStream(stream);
    setIsDialogOpen(true);
  };

  const handleNew = () => {
    setEditingStream(null);
    setIsDialogOpen(true);
  };

  if (loading) {
    return <div className="p-4">Загрузка потоков...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Потоки</h3>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={handleNew} disabled={classGroups.length === 0}>
              <Plus className="mr-2 h-4 w-4" />
              Новый поток
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {editingStream ? "Редактировать поток" : "Создать поток"}
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
                  name="class_group_ids"
                  render={() => (
                    <FormItem>
                      <div className="mb-4">
                        <FormLabel>Группы классов</FormLabel>
                        <p className="text-sm text-muted-foreground">
                          Выберите группы классов для включения в этот поток
                        </p>
                      </div>
                      {classGroups.map((classGroup) => (
                        <FormField
                          key={classGroup.id}
                          control={form.control}
                          name="class_group_ids"
                          render={({ field }) => {
                            return (
                              <FormItem
                                key={classGroup.id}
                                className="flex flex-row items-start space-x-3 space-y-0"
                              >
                                <FormControl>
                                  <Checkbox
                                    checked={field.value?.includes(
                                      classGroup.id,
                                    )}
                                    onCheckedChange={(checked: boolean) => {
                                      return checked
                                        ? field.onChange([
                                            ...field.value,
                                            classGroup.id,
                                          ])
                                        : field.onChange(
                                            field.value?.filter(
                                              (value) => value !== classGroup.id,
                                            ),
                                          );
                                    }}
                                  />
                                </FormControl>
                                <FormLabel className="font-normal">
                                  {classGroup.name} ({classGroup.student_count}{" "}
                                  студентов)
                                </FormLabel>
                              </FormItem>
                            );
                          }}
                        />
                      ))}
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
                      setEditingStream(null);
                    }}
                  >
                    Отмена
                  </Button>
                  <Button type="submit">
                    {editingStream ? "Обновить" : "Создать"}
                  </Button>
                </div>
              </form>
            </Form>
          </DialogContent>
        </Dialog>
      </div>

      {streams.length === 0 ? (
        <Card className="p-8 text-center">
          <Layers className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">
            Пока нет потоков. Создайте первый поток.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {streams.map((stream) => (
            <Card key={stream.id} className="p-4">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="font-semibold">{stream.name}</h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    {stream.class_groups.length} групп{stream.class_groups.length !== 1 ? "ы" : "а"} классов
                  </p>
                  {stream.class_groups.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs text-muted-foreground">
                        {stream.class_groups
                          .map((cg) => cg.name)
                          .join(", ")}
                      </p>
                    </div>
                  )}
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleEdit(stream)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(stream.id)}
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

export default StreamsTab;
