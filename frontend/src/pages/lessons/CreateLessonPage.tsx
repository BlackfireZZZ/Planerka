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
import { lessonsApi } from "@/api/lessons";
import { institutionsApi } from "@/api/institutions";
import type { Institution } from "@/api/institutions";
import axios from "axios";

const createLessonSchema = z.object({
  name: z.string().min(1, { message: "Название обязательно" }),
  subject_code: z.string().optional(),
  duration_minutes: z.number().min(1).max(480),
});

type CreateLessonFormValues = z.infer<typeof createLessonSchema>;

export const CreateLessonPage: React.FC = () => {
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

  const form = useForm<CreateLessonFormValues>({
    resolver: zodResolver(createLessonSchema),
    defaultValues: {
      name: "",
      subject_code: "",
      duration_minutes: 90,
    },
  });

  const onSubmit = async (data: CreateLessonFormValues) => {
    if (!institutionId) {
      setError("Пожалуйста, выберите учреждение");
      return;
    }
    try {
      setError(null);
      await lessonsApi.create(institutionId, {
        name: data.name,
        subject_code: data.subject_code || undefined,
        duration_minutes: data.duration_minutes,
      });
      navigate(`/institutions/${institutionId}`);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError("Не удалось создать урок");
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
          <CardTitle>Создать урок</CardTitle>
          <CardDescription>Введите данные нового урока</CardDescription>
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
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Название</FormLabel>
                    <FormControl>
                      <Input placeholder="Название урока" {...field} />
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
                    <FormLabel>Код предмета (Необязательно)</FormLabel>
                    <FormControl>
                      <Input placeholder="например, МАТ101" {...field} />
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
                        placeholder="90"
                        {...field}
                        onChange={(e) =>
                          field.onChange(parseInt(e.target.value) || 90)
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
