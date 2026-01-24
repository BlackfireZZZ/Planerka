import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { ArrowLeft, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { schedulesApi } from "@/api/schedules";
import { institutionsApi } from "@/api/institutions";
import type { Institution } from "@/api/institutions";

export const CreateSchedulePage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const institutionIdParam = searchParams.get("institution_id");

  const [institutionId, setInstitutionId] = useState<string>(
    institutionIdParam || "",
  );
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [name, setName] = useState("");
  const [academicPeriod, setAcademicPeriod] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingInstitutions, setLoadingInstitutions] = useState(true);

  useEffect(() => {
    loadInstitutions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadInstitutions = async () => {
    try {
      setLoadingInstitutions(true);
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
      setLoadingInstitutions(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!institutionId || !name.trim()) {
      alert("Пожалуйста, заполните все обязательные поля");
      return;
    }

    try {
      setLoading(true);
      const schedule = await schedulesApi.create(institutionId, {
        name: name.trim(),
        academic_period: academicPeriod.trim() || undefined,
      });
      navigate(`/schedules/${schedule.id}`);
    } catch (error) {
      console.error("Failed to create schedule:", error);
      alert("Не удалось создать расписание");
    } finally {
      setLoading(false);
    }
  };

  if (loadingInstitutions) {
    return <div className="p-8">Загрузка...</div>;
  }

  return (
    <div className="p-8">
      <div className="mb-6">
        <Button variant="outline" asChild>
          <Link to="/schedules">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Назад к расписаниям
          </Link>
        </Button>
      </div>

      <Card className="p-6 max-w-2xl">
        <h1 className="text-2xl font-bold mb-6">Создать новое расписание</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="institution">Учреждение *</Label>
            <select
              id="institution"
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

          <div>
            <Label htmlFor="name">Название расписания *</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="например, Расписание осень 2025"
              required
              className="mt-1"
            />
          </div>

          <div>
            <Label htmlFor="academic-period">Учебный период</Label>
            <Input
              id="academic-period"
              value={academicPeriod}
              onChange={(e) => setAcademicPeriod(e.target.value)}
              placeholder="например, Осень 2025, Весна 2026"
              className="mt-1"
            />
          </div>

          <div className="flex gap-2 pt-4">
            <Button
              type="submit"
              disabled={loading || !institutionId || !name.trim()}
            >
              <Save className="mr-2 h-4 w-4" />
              {loading ? "Создание..." : "Создать расписание"}
            </Button>
            <Button type="button" variant="outline" asChild>
              <Link to="/schedules">Отмена</Link>
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};
