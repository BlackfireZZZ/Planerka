import React, { useCallback, useEffect, useState } from "react";
import { BookOpen, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { classGroupsApi } from "@/api/classGroups";
import { studyGroupsApi } from "@/api/studyGroups";
import { lessonsApi } from "@/api/lessons";
import { streamsApi } from "@/api/streams";
import type { ClassGroup } from "@/api/classGroups";
import type { StudyGroup } from "@/api/studyGroups";
import type { Lesson } from "@/api/lessons";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import axios from "axios";

interface GroupLessonsTabProps {
  institutionId: string;
}

type AssigningGroup = { type: "class"; id: string; name: string } | { type: "study"; id: string; name: string };

export const GroupLessonsTab: React.FC<GroupLessonsTabProps> = ({
  institutionId,
}) => {
  const [classGroups, setClassGroups] = useState<ClassGroup[]>([]);
  const [studyGroups, setStudyGroups] = useState<StudyGroup[]>([]);
  const [streams, setStreams] = useState<Array<{ id: string; name: string }>>([]);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(true);
  const [assigning, setAssigning] = useState<AssigningGroup | null>(null);
  const [isAssignDialogOpen, setIsAssignDialogOpen] = useState(false);
  const [assigningLessonIds, setAssigningLessonIds] = useState<string[]>([]);
  const [loadingLessons, setLoadingLessons] = useState(false);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [cg, sg, less, str] = await Promise.all([
        classGroupsApi.list(institutionId),
        studyGroupsApi.list(institutionId),
        lessonsApi.list(institutionId),
        streamsApi.list(institutionId),
      ]);
      setClassGroups(cg);
      setStudyGroups(sg);
      setLessons(less);
      setStreams(str);
    } catch (error) {
      console.error("Failed to load data:", error);
    } finally {
      setLoading(false);
    }
  }, [institutionId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (isAssignDialogOpen && assigning) {
      setLoadingLessons(true);
      const fetch = assigning.type === "class"
        ? classGroupsApi.getLessons(assigning.id)
        : studyGroupsApi.getLessons(assigning.id);
      fetch
        .then((r) => {
          setAssigningLessonIds(r.map((x) => x.lesson_id));
        })
        .catch((err) => {
          console.error("Failed to load lessons for group:", err);
          setAssigningLessonIds([]);
        })
        .finally(() => {
          setLoadingLessons(false);
        });
    } else {
      setAssigningLessonIds([]);
    }
  }, [isAssignDialogOpen, assigning]);

  const getStreamName = (streamId: string) =>
    streams.find((s) => s.id === streamId)?.name ?? "—";

  const openAssign = (g: AssigningGroup) => {
    setAssigning(g);
    setIsAssignDialogOpen(true);
  };

  const handleAssignLessons = async (lessonIds: string[]) => {
    if (!assigning) return;
    try {
      if (assigning.type === "class") {
        await classGroupsApi.assignLessons(assigning.id, lessonIds);
      } else {
        await studyGroupsApi.assignLessons(assigning.id, lessonIds);
      }
      setIsAssignDialogOpen(false);
      setAssigning(null);
    } catch (error) {
      console.error("Failed to assign lessons:", error);
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        alert(String(error.response.data.detail));
      } else {
        alert("Не удалось назначить уроки");
      }
    }
  };

  const handleCancelAssign = () => {
    setIsAssignDialogOpen(false);
    setAssigning(null);
  };

  if (loading) {
    return <div className="p-4">Загрузка...</div>;
  }

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">Привязка уроков к группам</h3>

      {/* Section: Class groups */}
      <div>
        <h4 className="text-md font-medium mb-3">Группы классов</h4>
        {classGroups.length === 0 ? (
          <Card className="p-6 text-center">
            <Users className="h-10 w-10 mx-auto text-muted-foreground mb-2" />
            <p className="text-sm text-muted-foreground">
              Нет групп классов. Создайте группы в соответствующей вкладке.
            </p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {classGroups.map((cg) => (
              <Card key={cg.id} className="p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-semibold">{cg.name}</h4>
                    <p className="text-sm text-muted-foreground">
                      Студентов: {cg.student_count}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() =>
                      openAssign({ type: "class", id: cg.id, name: cg.name })
                    }
                    title="Назначить уроки"
                  >
                    <BookOpen className="h-4 w-4" />
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Section: Study groups */}
      <div>
        <h4 className="text-md font-medium mb-3">Учебные группы</h4>
        {studyGroups.length === 0 ? (
          <Card className="p-6 text-center">
            <Users className="h-10 w-10 mx-auto text-muted-foreground mb-2" />
            <p className="text-sm text-muted-foreground">
              Нет учебных групп. Создайте учебные группы в соответствующей
              вкладке.
            </p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {studyGroups.map((sg) => (
              <Card key={sg.id} className="p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-semibold">{sg.name}</h4>
                    <p className="text-sm text-muted-foreground">
                      Поток: {getStreamName(sg.stream_id)}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() =>
                      openAssign({ type: "study", id: sg.id, name: sg.name })
                    }
                    title="Назначить уроки"
                  >
                    <BookOpen className="h-4 w-4" />
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Assign lessons dialog */}
      <Dialog open={isAssignDialogOpen} onOpenChange={setIsAssignDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              Назначить уроки для {assigning?.name}
            </DialogTitle>
          </DialogHeader>
          <AssignLessonsForm
            lessons={lessons}
            selectedLessonIds={assigningLessonIds}
            loading={loadingLessons}
            onAssign={handleAssignLessons}
            onCancel={handleCancelAssign}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
};

interface AssignLessonsFormProps {
  lessons: Lesson[];
  selectedLessonIds: string[];
  loading: boolean;
  onAssign: (lessonIds: string[]) => void;
  onCancel: () => void;
}

const AssignLessonsForm: React.FC<AssignLessonsFormProps> = ({
  lessons,
  selectedLessonIds,
  loading,
  onAssign,
  onCancel,
}) => {
  const [selected, setSelected] = useState<Set<string>>(new Set(selectedLessonIds));

  useEffect(() => {
    setSelected(new Set(selectedLessonIds));
  }, [selectedLessonIds]);

  const handleToggle = (lessonId: string) => {
    const next = new Set(selected);
    if (next.has(lessonId)) next.delete(lessonId);
    else next.add(lessonId);
    setSelected(next);
  };

  const handleSubmit = () => {
    onAssign(Array.from(selected));
  };

  if (loading) {
    return <div className="p-4 text-sm text-muted-foreground">Загрузка…</div>;
  }

  return (
    <div className="space-y-4">
      <div className="max-h-60 overflow-y-auto space-y-2">
        {lessons.length === 0 ? (
          <p className="text-sm text-muted-foreground">Нет доступных уроков</p>
        ) : (
          lessons.map((lesson) => (
            <label
              key={lesson.id}
              className="flex items-center space-x-2 p-2 rounded hover:bg-accent cursor-pointer"
            >
              <input
                type="checkbox"
                checked={selected.has(lesson.id)}
                onChange={() => handleToggle(lesson.id)}
                className="rounded"
              />
              <div>
                <span className="text-sm font-medium">{lesson.name}</span>
                {lesson.subject_code && (
                  <span className="text-xs text-muted-foreground ml-2">
                    ({lesson.subject_code})
                  </span>
                )}
                <span className="text-xs text-muted-foreground ml-2">
                  {lesson.duration_minutes} min
                </span>
              </div>
            </label>
          ))
        )}
      </div>
      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={onCancel}>
          Отмена
        </Button>
        <Button onClick={handleSubmit}>Назначить</Button>
      </div>
    </div>
  );
};

export default GroupLessonsTab;
