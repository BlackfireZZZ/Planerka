import React, { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { timeSlotsApi } from "@/api/timeSlots";
import { institutionsApi } from "@/api/institutions";
import type { Institution } from "@/api/institutions";
import axios from "axios";

const createTimeSlotSchema = z.object({
  day_of_week: z.number().min(0).max(6),
  start_time: z.string().min(1, { message: "Время начала обязательно" }),
  end_time: z.string().min(1, { message: "Время окончания обязательно" }),
  slot_number: z.number().min(0),
});

type CreateTimeSlotFormValues = z.infer<typeof createTimeSlotSchema>;

const days = [
  { value: 0, label: "Понедельник" },
  { value: 1, label: "Вторник" },
  { value: 2, label: "Среда" },
  { value: 3, label: "Четверг" },
  { value: 4, label: "Пятница" },
  { value: 5, label: "Суббота" },
  { value: 6, label: "Воскресенье" },
];

export const CreateTimeSlotPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const institutionIdParam = searchParams.get("institution_id");

  const [institutionId, setInstitutionId] = useState<string>(
    institutionIdParam || "",
  );
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInstitutions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadInstitutions = async () => {
    try {
      const data = await institutionsApi.list();
      setInstitutions(data);
      if (institutionIdParam && data.some((i) => i.id === institutionIdParam)) {
        setInstitutionId(institutionIdParam);
      } else if (data.length > 0) {
        setInstitutionId(data[0].id);
      }
    } catch (error) {
      console.error("Failed to load institutions:", error);
    } finally {
      setLoading(false);
    }
  };

  const form = useForm<CreateTimeSlotFormValues>({
    resolver: zodResolver(createTimeSlotSchema),
    defaultValues: {
      day_of_week: 0,
      start_time: "09:00",
      end_time: "10:30",
      slot_number: 1,
    },
  });

  const onSubmit = async (data: CreateTimeSlotFormValues) => {
    if (!institutionId) {
      setError("Пожалуйста, выберите учреждение");
      return;
    }
    try {
      setError(null);
      await timeSlotsApi.create(institutionId, {
        day_of_week: data.day_of_week,
        start_time: data.start_time,
        end_time: data.end_time,
        slot_number: data.slot_number,
      });
      navigate(`/institutions/${institutionId}`);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError("Не удалось создать временной слот");
      }
    }
  };

  if (loading) {
    return <div className="p-8">Загрузка...</div>;
  }

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>Создать временной слот</CardTitle>
          <CardDescription>
            Введите данные нового временного слота
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <label
                  htmlFor="institution-select"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  Учреждение
                </label>
                <select
                  id="institution-select"
                  value={institutionId}
                  onChange={(e) => setInstitutionId(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md mt-1"
                  required
                >
                  <option value="">Выберите учреждение...</option>
                  {institutions.map((inst) => (
                    <option key={inst.id} value={inst.id}>
                      {inst.name}
                    </option>
                  ))}
                </select>
              </div>
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
                        {days.map((day) => (
                          <option key={day.value} value={day.value}>
                            {day.label}
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
                        placeholder="1"
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
              <div className="flex gap-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate("/institutions")}
                >
                  Отмена
                </Button>
                <Button
                  type="submit"
                  disabled={form.formState.isSubmitting || !institutionId}
                >
                  {form.formState.isSubmitting ? "Создание..." : "Создать"}
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
};
