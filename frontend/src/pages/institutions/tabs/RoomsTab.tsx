import React, { useEffect, useState } from "react";
import { Plus, Edit, Trash2, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { roomsApi } from "@/api/rooms";
import type { Room } from "@/api/rooms";
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

const roomSchema = z.object({
  name: z.string().min(1, "Название обязательно"),
  capacity: z.number().min(1),
  room_type: z.string().optional(),
  equipment: z.string().optional(),
});

type RoomFormValues = z.infer<typeof roomSchema>;

interface RoomsTabProps {
  institutionId: string;
}

export const RoomsTab: React.FC<RoomsTabProps> = ({ institutionId }) => {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingRoom, setEditingRoom] = useState<Room | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  useEffect(() => {
    loadRooms();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [institutionId]);

  const loadRooms = async () => {
    try {
      setLoading(true);
      const data = await roomsApi.list(institutionId);
      setRooms(data);
    } catch (error) {
      console.error("Failed to load rooms:", error);
    } finally {
      setLoading(false);
    }
  };

  const form = useForm<RoomFormValues>({
    resolver: zodResolver(roomSchema),
    defaultValues: {
      name: "",
      capacity: 1,
      room_type: "",
      equipment: "",
    },
  });

  useEffect(() => {
    if (editingRoom) {
      form.reset({
        name: editingRoom.name,
        capacity: editingRoom.capacity,
        room_type: editingRoom.room_type || "",
        equipment: editingRoom.equipment || "",
      });
    } else {
      form.reset({
        name: "",
        capacity: 1,
        room_type: "",
        equipment: "",
      });
    }
  }, [editingRoom, form]);

  const onSubmit = async (data: RoomFormValues) => {
    try {
      if (editingRoom) {
        await roomsApi.update(editingRoom.id, data);
      } else {
        await roomsApi.create(institutionId, data);
      }
      setIsDialogOpen(false);
      setEditingRoom(null);
      await loadRooms();
    } catch (error) {
      console.error("Failed to save room:", error);
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        alert(error.response.data.detail);
      } else {
        alert("Не удалось сохранить аудиторию");
      }
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Вы уверены, что хотите удалить эту аудиторию?")) return;
    try {
      await roomsApi.delete(id);
      await loadRooms();
    } catch (error) {
      console.error("Failed to delete room:", error);
      alert("Не удалось удалить аудиторию");
    }
  };

  const handleEdit = (room: Room) => {
    setEditingRoom(room);
    setIsDialogOpen(true);
  };

  const handleNew = () => {
    setEditingRoom(null);
    setIsDialogOpen(true);
  };

  if (loading) {
    return <div className="p-4">Загрузка аудиторий...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Аудитории</h3>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={handleNew}>
              <Plus className="mr-2 h-4 w-4" />
              Новая аудитория
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {editingRoom ? "Редактировать аудиторию" : "Создать аудиторию"}
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
                  name="capacity"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Вместимость</FormLabel>
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
                <FormField
                  control={form.control}
                  name="room_type"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Тип аудитории</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="equipment"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Оборудование</FormLabel>
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
                      setEditingRoom(null);
                    }}
                  >
                    Отмена
                  </Button>
                  <Button type="submit">
                    {editingRoom ? "Обновить" : "Создать"}
                  </Button>
                </div>
              </form>
            </Form>
          </DialogContent>
        </Dialog>
      </div>

      {rooms.length === 0 ? (
        <Card className="p-8 text-center">
          <MapPin className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">
            Пока нет аудиторий. Создайте первую аудиторию.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {rooms.map((room) => (
            <Card key={room.id} className="p-4">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="font-semibold">{room.name}</h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    Вместимость: {room.capacity}
                  </p>
                  {room.room_type && (
                    <p className="text-sm text-muted-foreground">
                      Тип: {room.room_type}
                    </p>
                  )}
                  {room.equipment && (
                    <p className="text-sm text-muted-foreground">
                      Оборудование: {room.equipment}
                    </p>
                  )}
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleEdit(room)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(room.id)}
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

export default RoomsTab;
