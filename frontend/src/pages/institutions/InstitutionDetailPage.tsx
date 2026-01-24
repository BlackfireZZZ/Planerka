import React, { useEffect, useRef, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Building2, ArrowLeft, Edit, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { institutionsApi } from "@/api/institutions";
import type { Institution } from "@/api/institutions";
import { LessonsTab } from "./tabs/LessonsTab";
import { TeachersTab } from "./tabs/TeachersTab";
import { ClassGroupsTab } from "./tabs/ClassGroupsTab";
import { StreamsTab } from "./tabs/StreamsTab";
import { StudyGroupsTab } from "./tabs/StudyGroupsTab";
import { RoomsTab } from "./tabs/RoomsTab";
import { TimeSlotsTab } from "./tabs/TimeSlotsTab";
import { StudentsTab } from "./tabs/StudentsTab";
import { ConstraintsTab } from "./tabs/ConstraintsTab";
import { SchedulesTab } from "./tabs/SchedulesTab";
import { GroupLessonsTab } from "./tabs/GroupLessonsTab";

export const InstitutionDetailPage: React.FC = () => {
  const { institutionId } = useParams<{ institutionId: string }>();
  const navigate = useNavigate();
  const [institution, setInstitution] = useState<Institution | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const tabsListRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (institutionId) {
      loadInstitution();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [institutionId]);

  useEffect(() => {
    const el = tabsListRef.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      if (el.scrollWidth <= el.clientWidth) return;
      el.scrollLeft += e.deltaY;
      e.preventDefault();
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, [loading, institution]);

  const loadInstitution = async () => {
    if (!institutionId) return;
    try {
      setLoading(true);
      const data = await institutionsApi.get(institutionId);
      setInstitution(data);
    } catch (error) {
      console.error("Failed to load institution:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!institutionId) return;
    if (!confirm("Вы уверены, что хотите удалить это учреждение?")) {
      return;
    }
    try {
      setDeleting(true);
      await institutionsApi.delete(institutionId);
      navigate("/institutions");
    } catch (error) {
      console.error("Failed to delete institution:", error);
      alert("Не удалось удалить учреждение");
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return <div className="p-8">Загрузка...</div>;
  }

  if (!institution) {
    return (
      <div className="p-8">
        <div className="mb-4">
          <Button variant="outline" asChild>
            <Link to="/institutions">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Назад к учреждениям
            </Link>
          </Button>
        </div>
        <Card className="p-12 text-center">
          <Building2 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">Учреждение не найдено</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-6">
        <Button variant="outline" asChild>
          <Link to="/institutions">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Назад к учреждениям
          </Link>
        </Button>
      </div>

      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center space-x-3">
          <Building2 className="h-10 w-10 text-blue-500" />
          <div>
            <h1 className="text-3xl font-bold">{institution.name}</h1>
            <p className="text-muted-foreground">
              Создано: {new Date(institution.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" disabled>
            <Edit className="mr-2 h-4 w-4" />
            Редактировать
          </Button>
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={deleting}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            {deleting ? "Удаление..." : "Удалить"}
          </Button>
        </div>
      </div>

      <Card className="p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Информация об учреждении</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-muted-foreground">ID</p>
            <p className="font-semibold">{institution.id}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Название</p>
            <p className="font-semibold">{institution.name}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Создано</p>
            <p className="font-semibold">
              {new Date(institution.created_at).toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Обновлено</p>
            <p className="font-semibold">
              {new Date(institution.updated_at).toLocaleString()}
            </p>
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <Tabs defaultValue="lessons" className="w-full">
          <TabsList
            ref={tabsListRef}
            className="tabs-list-scroll flex w-full min-w-0 flex-nowrap justify-start overflow-x-auto overflow-y-hidden [&_button]:shrink-0"
          >
            <TabsTrigger value="lessons">Уроки</TabsTrigger>
            <TabsTrigger value="teachers">Преподаватели</TabsTrigger>
            <TabsTrigger value="class-groups">Классы</TabsTrigger>
            <TabsTrigger value="students">Студенты</TabsTrigger>
            <TabsTrigger value="streams">Потоки</TabsTrigger>
            <TabsTrigger value="study-groups">Учебные группы</TabsTrigger>
            <TabsTrigger value="group-lessons">Привязка уроков</TabsTrigger>
            <TabsTrigger value="rooms">Аудитории</TabsTrigger>
            <TabsTrigger value="time-slots">Временные слоты</TabsTrigger>
            <TabsTrigger value="constraints">Ограничения</TabsTrigger>
            <TabsTrigger value="schedules">Расписания</TabsTrigger>
          </TabsList>
          <TabsContent value="lessons" className="mt-4">
            <LessonsTab institutionId={institution.id} />
          </TabsContent>
          <TabsContent value="teachers" className="mt-4">
            <TeachersTab institutionId={institution.id} />
          </TabsContent>
          <TabsContent value="class-groups" className="mt-4">
            <ClassGroupsTab institutionId={institution.id} />
          </TabsContent>
          <TabsContent value="streams" className="mt-4">
            <StreamsTab institutionId={institution.id} />
          </TabsContent>
          <TabsContent value="study-groups" className="mt-4">
            <StudyGroupsTab institutionId={institution.id} />
          </TabsContent>
          <TabsContent value="students" className="mt-4">
            <StudentsTab institutionId={institution.id} />
          </TabsContent>
          <TabsContent value="group-lessons" className="mt-4">
            <GroupLessonsTab institutionId={institution.id} />
          </TabsContent>
          <TabsContent value="rooms" className="mt-4">
            <RoomsTab institutionId={institution.id} />
          </TabsContent>
          <TabsContent value="time-slots" className="mt-4">
            <TimeSlotsTab institutionId={institution.id} />
          </TabsContent>
          <TabsContent value="constraints" className="mt-4">
            <ConstraintsTab institutionId={institution.id} />
          </TabsContent>
          <TabsContent value="schedules" className="mt-4">
            <SchedulesTab institutionId={institution.id} />
          </TabsContent>
        </Tabs>
      </Card>
    </div>
  );
};

export default InstitutionDetailPage;
