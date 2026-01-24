import { apiClient } from "./client";

export interface Lesson {
  id: string;
  institution_id: string;
  name: string;
  subject_code: string | null;
  duration_minutes: number;
  created_at: string;
  updated_at: string;
}

export interface LessonCreate {
  name: string;
  subject_code?: string;
  duration_minutes: number;
}

export interface LessonUpdate {
  name?: string;
  subject_code?: string;
  duration_minutes?: number;
}

export const lessonsApi = {
  create: async (
    institutionId: string,
    data: LessonCreate,
  ): Promise<Lesson> => {
    const response = await apiClient.post<Lesson>(
      `/api/v1/lessons?institution_id=${institutionId}`,
      data,
    );
    return response.data;
  },

  list: async (institutionId: string): Promise<Lesson[]> => {
    const response = await apiClient.get<Lesson[]>(
      `/api/v1/lessons?institution_id=${institutionId}`,
    );
    return response.data;
  },

  get: async (id: string): Promise<Lesson> => {
    const response = await apiClient.get<Lesson>(`/api/v1/lessons/${id}`);
    return response.data;
  },

  update: async (id: string, data: LessonUpdate): Promise<Lesson> => {
    const response = await apiClient.put<Lesson>(`/api/v1/lessons/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/lessons/${id}`);
  },
};
