import { apiClient } from "./client";

export interface ScheduleEntry {
  id: string;
  institution_id: string;
  schedule_id: string;
  lesson_id: string;
  teacher_id: number;
  class_group_id: string | null;
  study_group_id: string | null;
  room_id: string;
  time_slot_id: string;
  week_number: number | null;
  created_at: string;
  updated_at: string;
}

export interface Schedule {
  id: string;
  institution_id: string;
  name: string;
  academic_period: string | null;
  status: "draft" | "generated" | "active";
  generated_at: string | null;
  created_at: string;
  updated_at: string;
  entries: ScheduleEntry[];
  entries_count?: number;
}

export interface ScheduleCreate {
  name: string;
  academic_period?: string;
}

export interface ScheduleUpdate {
  name?: string;
  academic_period?: string;
  status?: "draft" | "generated" | "active";
}

export interface ScheduleGenerateRequest {
  timeout?: number;
}

export interface ScheduleGenerateResponse {
  success: boolean;
  message: string;
  entries_count: number | null;
}

export interface SchedulePdfExportResponse {
  url: string;
  filename: string;
}

export const schedulesApi = {
  create: async (
    institutionId: string,
    data: ScheduleCreate,
  ): Promise<Schedule> => {
    const response = await apiClient.post<Schedule>(
      `/api/v1/schedules?institution_id=${institutionId}`,
      data,
    );
    return response.data;
  },

  list: async (institutionId: string): Promise<Schedule[]> => {
    const response = await apiClient.get<Schedule[]>(
      `/api/v1/schedules?institution_id=${institutionId}`,
    );
    return response.data;
  },

  get: async (id: string): Promise<Schedule> => {
    const response = await apiClient.get<Schedule>(`/api/v1/schedules/${id}`);
    return response.data;
  },

  /** Расписание + все справочники одним запросом (вместо 8 вызовов). */
  getWithReferences: async (
    id: string,
  ): Promise<{
    schedule: Schedule;
    time_slots: import("./timeSlots").TimeSlot[];
    lessons: import("./lessons").Lesson[];
    teachers: import("./teachers").Teacher[];
    rooms: import("./rooms").Room[];
    class_groups: import("./classGroups").ClassGroup[];
    study_groups: import("./studyGroups").StudyGroup[];
    students: import("./students").Student[];
  }> => {
    const response = await apiClient.get(
      `/api/v1/schedules/${id}/with-references`,
    );
    return response.data;
  },

  update: async (id: string, data: ScheduleUpdate): Promise<Schedule> => {
    const response = await apiClient.put<Schedule>(
      `/api/v1/schedules/${id}`,
      data,
    );
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/schedules/${id}`);
  },

  generate: async (
    id: string,
    request: ScheduleGenerateRequest = {},
  ): Promise<ScheduleGenerateResponse> => {
    const response = await apiClient.post<ScheduleGenerateResponse>(
      `/api/v1/schedules/${id}/generate`,
      request,
    );
    return response.data;
  },

  exportPdf: async (id: string): Promise<SchedulePdfExportResponse> => {
    const response = await apiClient.get<SchedulePdfExportResponse>(
      `/api/v1/schedules/${id}/export/pdf`,
    );
    return response.data;
  },
};
