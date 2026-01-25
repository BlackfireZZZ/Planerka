import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Calendar, Building2, Users, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { institutionsApi } from "@/api/institutions";
import { classGroupsApi } from "@/api/classGroups";
import { schedulesApi } from "@/api/schedules";
import { lessonsApi } from "@/api/lessons";
import type { Institution } from "@/api/institutions";

export const DashboardPage: React.FC = () => {
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [institutionsCount, setInstitutionsCount] = useState<number>(0);
  const [schedulesCount, setSchedulesCount] = useState<number>(0);
  const [classGroupsCount, setClassGroupsCount] = useState<number>(0);
  const [lessonsCount, setLessonsCount] = useState<number>(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);

      // Загрузить все учреждения
      const institutionsData = await institutionsApi.list();
      setInstitutions(institutionsData);
      setInstitutionsCount(institutionsData.length);

      // Загрузить расписания, группы классов и уроки для всех учреждений
      let totalSchedules = 0;
      let totalClassGroups = 0;
      let totalLessons = 0;

      // Обработать все учреждения параллельно
      const promises = institutionsData.map(
        async (institution: Institution) => {
          try {
            // Загрузить расписания
            const schedules = await schedulesApi.list(institution.id);
            totalSchedules += schedules.length;

            // Загрузить группы классов
            const classGroups = await classGroupsApi.list(institution.id);
            totalClassGroups += classGroups.length;

            // Загрузить уроки
            const lessons = await lessonsApi.list(institution.id);
            totalLessons += lessons.length;
          } catch (error) {
            console.error(
              `Failed to load data for institution ${institution.id}:`,
              error,
            );
          }
        },
      );

      await Promise.all(promises);

      setSchedulesCount(totalSchedules);
      setClassGroupsCount(totalClassGroups);
      setLessonsCount(totalLessons);
    } catch (error) {
      console.error("Failed to load dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8">
        <h1 className="text-3xl font-bold mb-6">Панель управления</h1>
        <div className="text-center py-12">
          <p className="text-muted-foreground">
            Загрузка данных панели управления...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">Панель управления</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Учреждения</p>
              <p className="text-2xl font-bold">{institutionsCount}</p>
            </div>
            <Building2 className="h-8 w-8 text-blue-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Расписания</p>
              <p className="text-2xl font-bold">{schedulesCount}</p>
            </div>
            <Calendar className="h-8 w-8 text-green-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Группы классов</p>
              <p className="text-2xl font-bold">{classGroupsCount}</p>
            </div>
            <Users className="h-8 w-8 text-purple-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Уроки</p>
              <p className="text-2xl font-bold">{lessonsCount}</p>
            </div>
            <BookOpen className="h-8 w-8 text-orange-500" />
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Быстрые действия</h2>
          <div className="space-y-3">
            <Link to="/institutions">
              <Button className="w-full" variant="outline">
                <Building2 className="mr-2 h-4 w-4" />
                Управление учреждениями
              </Button>
            </Link>
            <Link to="/schedules">
              <Button className="w-full" variant="outline">
                <Calendar className="mr-2 h-4 w-4" />
                Управление расписаниями
              </Button>
            </Link>
          </div>
        </Card>

        {institutionsCount === 0 ? (
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Начать работу</h2>
            <p className="text-muted-foreground mb-4">
              У вас пока нет учреждений. Создайте первое учреждение, чтобы
              начать управлять расписаниями.
            </p>
            <Link to="/institutions/new">
              <Button className="w-full">
                <Building2 className="mr-2 h-4 w-4" />
                Создать первое учреждение
              </Button>
            </Link>
          </Card>
        ) : (
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Создать новое</h2>
            <div className="space-y-2">
              <Link to="/institutions/new">
                <Button className="w-full" variant="outline" size="sm">
                  <Building2 className="mr-2 h-4 w-4" />
                  Новое учреждение
                </Button>
              </Link>
              {institutions.length > 0 && (
                <>
                  <Link
                    to={`/schedules/new?institution_id=${institutions[0].id}`}
                  >
                    <Button className="w-full" variant="outline" size="sm">
                      <Calendar className="mr-2 h-4 w-4" />
                      Новое расписание
                    </Button>
                  </Link>
                  <Link
                    to={`/class-groups/new?institution_id=${institutions[0].id}`}
                  >
                    <Button className="w-full" variant="outline" size="sm">
                      <Users className="mr-2 h-4 w-4" />
                      Новая группа класса
                    </Button>
                  </Link>
                  <Link
                    to={`/lessons/new?institution_id=${institutions[0].id}`}
                  >
                    <Button className="w-full" variant="outline" size="sm">
                      <BookOpen className="mr-2 h-4 w-4" />
                      Новый урок
                    </Button>
                  </Link>
                </>
              )}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};
