import React, { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Plus, Calendar, Download, Building2, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { schedulesApi } from "@/api/schedules";
import { institutionsApi } from "@/api/institutions";
import type { Schedule } from "@/api/schedules";
import type { Institution } from "@/api/institutions";

export const SchedulesPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const institutionId = searchParams.get("institution_id");

  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [selectedInstitutionId, setSelectedInstitutionId] = useState<
    string | null
  >(institutionId);
  const [loading, setLoading] = useState(true);
  const [loadingInstitutions, setLoadingInstitutions] = useState(true);

  useEffect(() => {
    loadInstitutions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (selectedInstitutionId) {
      loadSchedules(selectedInstitutionId);
      setSearchParams({ institution_id: selectedInstitutionId });
    } else {
      setSchedules([]);
      setLoading(false);
    }
  }, [selectedInstitutionId, setSearchParams]);

  const loadInstitutions = async () => {
    try {
      setLoadingInstitutions(true);
      const data = await institutionsApi.list();
      setInstitutions(data);
      if (data.length > 0 && !selectedInstitutionId) {
        setSelectedInstitutionId(data[0].id);
      }
    } catch (error) {
      console.error("Failed to load institutions:", error);
    } finally {
      setLoadingInstitutions(false);
    }
  };

  const loadSchedules = async (instId: string) => {
    try {
      setLoading(true);
      const data = await schedulesApi.list(instId);
      setSchedules(data);
    } catch (error) {
      console.error("Failed to load schedules:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleExportPdf = async (scheduleId: string) => {
    try {
      const result = await schedulesApi.exportPdf(scheduleId);
      // Открыть предварительно подписанный URL в новой вкладке для загрузки
      const a = document.createElement("a");
      a.href = result.url;
      a.download = result.filename;
      a.target = "_blank";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch (error) {
      console.error("Failed to export PDF:", error);
      alert("Не удалось экспортировать PDF");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Вы уверены, что хотите удалить это расписание?")) return;
    try {
      await schedulesApi.delete(id);
      if (selectedInstitutionId) {
        await loadSchedules(selectedInstitutionId);
      }
    } catch (error) {
      console.error("Failed to delete schedule:", error);
      alert("Не удалось удалить расписание");
    }
  };

  if (loadingInstitutions) {
    return <div className="p-8">Загрузка...</div>;
  }

  if (institutions.length === 0) {
    return (
      <div className="p-8">
        <Card className="p-12 text-center">
          <Building2 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground mb-4">Учреждения не найдены</p>
          <Button asChild>
            <Link to="/institutions/new">Создать первое учреждение</Link>
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Расписания</h1>
        {selectedInstitutionId && (
          <Button asChild>
            <Link to={`/schedules/new?institution_id=${selectedInstitutionId}`}>
              <Plus className="mr-2 h-4 w-4" />
              Создать расписание
            </Link>
          </Button>
        )}
      </div>

      <Card className="p-4 mb-6">
        <div className="flex items-center gap-4">
          <label htmlFor="institution-select" className="font-medium">
            Учреждение:
          </label>
          <select
            id="institution-select"
            value={selectedInstitutionId || ""}
            onChange={(e) => setSelectedInstitutionId(e.target.value || null)}
            className="px-3 py-2 border rounded-md min-w-[200px]"
          >
            <option value="">Выберите учреждение...</option>
            {institutions.map((inst) => (
              <option key={inst.id} value={inst.id}>
                {inst.name}
              </option>
            ))}
          </select>
        </div>
      </Card>

      {loading ? (
        <div className="p-8 text-center">Загрузка расписаний...</div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {schedules.map((schedule) => (
              <Card key={schedule.id} className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg">{schedule.name}</h3>
                    {schedule.academic_period && (
                      <p className="text-sm text-muted-foreground">
                        {schedule.academic_period}
                      </p>
                    )}
                    <p className="text-xs text-muted-foreground mt-1">
                      Статус:{" "}
                      <span className="capitalize">{schedule.status}</span>
                    </p>
                    {(schedule.entries_count ?? schedule.entries?.length ?? 0) > 0 && (
                      <p className="text-xs text-muted-foreground">
                        {schedule.entries_count ?? schedule.entries?.length ?? 0} записей
                      </p>
                    )}
                  </div>
                  <Calendar className="h-6 w-6 text-blue-500 flex-shrink-0" />
                </div>
                <div className="space-y-2">
                  <Link to={`/schedules/${schedule.id}`}>
                    <Button variant="outline" className="w-full">
                      Открыть
                    </Button>
                  </Link>
                  {schedule.status === "generated" && (
                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={() => handleExportPdf(schedule.id)}
                    >
                      <Download className="mr-2 h-4 w-4" />
                      Экспорт PDF
                    </Button>
                  )}
                  <Button
                    variant="destructive"
                    className="w-full"
                    onClick={() => handleDelete(schedule.id)}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Удалить
                  </Button>
                </div>
              </Card>
            ))}
          </div>

          {!loading && schedules.length === 0 && selectedInstitutionId && (
            <Card className="p-12 text-center">
              <Calendar className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground mb-4">Расписания не найдены</p>
              <Button asChild>
                <Link
                  to={`/schedules/new?institution_id=${selectedInstitutionId}`}
                >
                  Создать первое расписание
                </Link>
              </Button>
            </Card>
          )}
        </>
      )}
    </div>
  );
};
