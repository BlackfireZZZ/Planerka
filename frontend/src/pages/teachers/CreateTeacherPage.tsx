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
import { teachersApi } from "@/api/teachers";
import { institutionsApi } from "@/api/institutions";
import type { Institution } from "@/api/institutions";
import axios from "axios";

const createTeacherSchema = z.object({
  full_name: z.string().min(1, { message: "Полное имя обязательно" }),
  subject: z.string().optional(),
});

type CreateTeacherFormValues = z.infer<typeof createTeacherSchema>;

export const CreateTeacherPage: React.FC = () => {
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

  const form = useForm<CreateTeacherFormValues>({
    resolver: zodResolver(createTeacherSchema),
    defaultValues: {
      full_name: "",
      subject: "",
    },
  });

  const onSubmit = async (data: CreateTeacherFormValues) => {
    if (!institutionId) {
      setError("Пожалуйста, выберите учреждение");
      return;
    }
    try {
      setError(null);
      await teachersApi.create(institutionId, {
        full_name: data.full_name,
        subject: data.subject || undefined,
      });
      navigate(`/institutions/${institutionId}`);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError("Не удалось создать преподавателя");
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
          <CardTitle>Создать преподавателя</CardTitle>
          <CardDescription>
            Введите данные нового преподавателя
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
                name="full_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Полное имя</FormLabel>
                    <FormControl>
                      <Input placeholder="Полное имя преподавателя" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="subject"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Предмет (Необязательно)</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="например, Математика, Физика"
                        {...field}
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
