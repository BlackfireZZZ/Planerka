import { apiClient } from "./client";

export interface Teacher {
  id: number;
  institution_id: string;
  full_name: string;
  subject: string | null;
  created_at: string;
  updated_at: string;
}

export interface TeacherCreate {
  full_name: string;
  subject?: string;
}

export interface TeacherUpdate {
  full_name?: string;
  subject?: string;
}

export const teachersApi = {
  create: async (
    institutionId: string,
    data: TeacherCreate,
  ): Promise<Teacher> => {
    const response = await apiClient.post<Teacher>(
      `/api/v1/teachers?institution_id=${institutionId}`,
      data,
    );
    return response.data;
  },

  list: async (institutionId: string): Promise<Teacher[]> => {
    const response = await apiClient.get<Teacher[]>(
      `/api/v1/teachers?institution_id=${institutionId}`,
    );
    return response.data;
  },

  get: async (id: number): Promise<Teacher> => {
    const response = await apiClient.get<Teacher>(`/api/v1/teachers/${id}`);
    return response.data;
  },

  update: async (id: number, data: TeacherUpdate): Promise<Teacher> => {
    const response = await apiClient.put<Teacher>(
      `/api/v1/teachers/${id}`,
      data,
    );
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/v1/teachers/${id}`);
  },

  assignLessons: async (
    teacherId: number,
    lessonIds: string[],
  ): Promise<void> => {
    await apiClient.post(`/api/v1/teachers/${teacherId}/assign-lessons`, {
      lesson_ids: lessonIds,
    });
  },

  getLessons: async (
    teacherId: number,
  ): Promise<
    { id: string; teacher_id: number; lesson_id: string; created_at: string }[]
  > => {
    const response = await apiClient.get(
      `/api/v1/teachers/${teacherId}/lessons`,
    );
    return response.data;
  },
};
