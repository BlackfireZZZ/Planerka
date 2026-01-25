import React, { useEffect, useState } from "react";
import { Plus, Calendar, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { schedulesApi } from "@/api/schedules";
import type { Schedule } from "@/api/schedules";
import { Link } from "react-router-dom";

interface SchedulesTabProps {
  institutionId: string;
}

export const SchedulesTab: React.FC<SchedulesTabProps> = ({
  institutionId,
}) => {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSchedules();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [institutionId]);

  const loadSchedules = async () => {
    try {
      setLoading(true);
      const data = await schedulesApi.list(institutionId);
      setSchedules(data);
    } catch (error) {
      console.error("Failed to load schedules:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Вы уверены, что хотите удалить это расписание?")) return;
    try {
      await schedulesApi.delete(id);
      await loadSchedules();
    } catch (error) {
      console.error("Failed to delete schedule:", error);
      alert("Не удалось удалить расписание");
    }
  };

  if (loading) {
    return <div className="p-4">Загрузка расписаний...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Расписания</h3>
        <Button asChild>
          <Link to={`/schedules/new?institution_id=${institutionId}`}>
            <Plus className="mr-2 h-4 w-4" />
            Новое расписание
          </Link>
        </Button>
      </div>

      {schedules.length === 0 ? (
        <Card className="p-8 text-center">
          <Calendar className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">
            Пока нет расписаний. Создайте первое расписание.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {schedules.map((schedule) => (
            <Card key={schedule.id} className="p-4">
              <div className="flex justify-between items-start mb-2">
                <div className="flex-1">
                  <Link to={`/schedules/${schedule.id}`}>
                    <h4 className="font-semibold hover:text-primary">
                      {schedule.name}
                    </h4>
                  </Link>
                  <p className="text-sm text-muted-foreground mt-1">
                    Записей:{" "}
                    {schedule.entries_count ?? schedule.entries?.length ?? 0}
                  </p>
                  {schedule.status && (
                    <p className="text-sm text-muted-foreground">
                      Статус: {schedule.status}
                    </p>
                  )}
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(schedule.id)}
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

export default SchedulesTab;
