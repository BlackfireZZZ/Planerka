import React, { useEffect, useState } from "react";
import { Plus, Edit, Trash2, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { timeSlotsApi } from "@/api/timeSlots";
import type { TimeSlot } from "@/api/timeSlots";
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

const timeSlotSchema = z.object({
  day_of_week: z.number().min(0).max(6),
  start_time: z.string().min(1, "Время начала обязательно"),
  end_time: z.string().min(1, "Время окончания обязательно"),
  slot_number: z.number().min(1),
});

type TimeSlotFormValues = z.infer<typeof timeSlotSchema>;

const DAYS = [
  "Понедельник",
  "Вторник",
  "Среда",
  "Четверг",
  "Пятница",
  "Суббота",
  "Воскресенье",
];

interface TimeSlotsTabProps {
  institutionId: string;
}

export const TimeSlotsTab: React.FC<TimeSlotsTabProps> = ({
  institutionId,
}) => {
  const [timeSlots, setTimeSlots] = useState<TimeSlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingTimeSlot, setEditingTimeSlot] = useState<TimeSlot | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  useEffect(() => {
    loadTimeSlots();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [institutionId]);

  const loadTimeSlots = async () => {
    try {
      setLoading(true);
      const data = await timeSlotsApi.list(institutionId);
      setTimeSlots(data);
    } catch (error) {
      console.error("Failed to load time slots:", error);
    } finally {
      setLoading(false);
    }
  };

  const form = useForm<TimeSlotFormValues>({
    resolver: zodResolver(timeSlotSchema),
    defaultValues: {
      day_of_week: 0,
      start_time: "09:00",
      end_time: "10:30",
      slot_number: 1,
    },
  });

  useEffect(() => {
    if (editingTimeSlot) {
      form.reset({
        day_of_week: editingTimeSlot.day_of_week,
        start_time: editingTimeSlot.start_time,
        end_time: editingTimeSlot.end_time,
        slot_number: editingTimeSlot.slot_number,
      });
    } else {
      form.reset({
        day_of_week: 0,
        start_time: "09:00",
        end_time: "10:30",
        slot_number: 1,
      });
    }
  }, [editingTimeSlot, form]);

  const onSubmit = async (data: TimeSlotFormValues) => {
    try {
      if (editingTimeSlot) {
        await timeSlotsApi.update(editingTimeSlot.id, data);
      } else {
        await timeSlotsApi.create(institutionId, data);
      }
      setIsDialogOpen(false);
      setEditingTimeSlot(null);
      await loadTimeSlots();
    } catch (error) {
      console.error("Failed to save time slot:", error);
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        alert(error.response.data.detail);
      } else {
        alert("Не удалось сохранить временной слот");
      }
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Вы уверены, что хотите удалить этот временной слот?")) return;
    try {
      await timeSlotsApi.delete(id);
      await loadTimeSlots();
    } catch (error) {
      console.error("Failed to delete time slot:", error);
      alert("Не удалось удалить временной слот");
    }
  };

  const handleEdit = (timeSlot: TimeSlot) => {
    setEditingTimeSlot(timeSlot);
    setIsDialogOpen(true);
  };

  const handleNew = () => {
    setEditingTimeSlot(null);
    setIsDialogOpen(true);
  };

  if (loading) {
    return <div className="p-4">Загрузка временных слотов...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Временные слоты</h3>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={handleNew}>
              <Plus className="mr-2 h-4 w-4" />
              Новый временной слот
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {editingTimeSlot ? "Редактировать временной слот" : "Создать временной слот"}
              </DialogTitle>
            </DialogHeader>
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="space-y-4"
              >
                <FormField
                  control={form.control}
                  name="day_of_week"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>День недели</FormLabel>
                      <FormControl>
                        <select
                          {...field}
                          onChange={(e) =>
                            field.onChange(parseInt(e.target.value))
                          }
                          className="w-full px-3 py-2 border rounded-md"
                        >
                          {DAYS.map((day, index) => (
                            <option key={index} value={index}>
                              {day}
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
                  name="start_time"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Время начала</FormLabel>
                      <FormControl>
                        <Input type="time" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="end_time"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Время окончания</FormLabel>
                      <FormControl>
                        <Input type="time" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="slot_number"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Номер слота</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          {...field}
                          onChange={(e) =>
                            field.onChange(parseInt(e.target.value) || 1)
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
                      setEditingTimeSlot(null);
                    }}
                  >
                    Отмена
                  </Button>
                  <Button type="submit">
                    {editingTimeSlot ? "Обновить" : "Создать"}
                  </Button>
                </div>
              </form>
            </Form>
          </DialogContent>
        </Dialog>
      </div>

      {timeSlots.length === 0 ? (
        <Card className="p-8 text-center">
          <Clock className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">
            Пока нет временных слотов. Создайте первый временной слот.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {timeSlots.map((timeSlot) => (
            <Card key={timeSlot.id} className="p-4">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="font-semibold">
                    {DAYS[timeSlot.day_of_week]}
                  </h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    {timeSlot.start_time} - {timeSlot.end_time}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Slot
                  </p>
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleEdit(timeSlot)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(timeSlot.id)}
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

export default TimeSlotsTab;
