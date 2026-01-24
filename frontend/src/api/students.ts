import { apiClient } from "./client";

export interface Student {
  id: string;
  institution_id: string;
  class_group_id: string;
  full_name: string;
  student_number: string | null;
  created_at: string;
  updated_at: string;
}

export interface StudentCreate {
  class_group_id: string;
  full_name: string;
  student_number?: string;
}

export interface StudentUpdate {
  class_group_id?: string;
  full_name?: string;
  student_number?: string;
}

export const studentsApi = {
  create: async (
    institutionId: string,
    data: StudentCreate,
  ): Promise<Student> => {
    const response = await apiClient.post<Student>(
      `/api/v1/students?institution_id=${institutionId}`,
      data,
    );
    return response.data;
  },

  list: async (institutionId: string): Promise<Student[]> => {
    const response = await apiClient.get<Student[]>(
      `/api/v1/students?institution_id=${institutionId}`,
    );
    return response.data;
  },

  get: async (id: string): Promise<Student> => {
    const response = await apiClient.get<Student>(`/api/v1/students/${id}`);
    return response.data;
  },

  update: async (id: string, data: StudentUpdate): Promise<Student> => {
    const response = await apiClient.put<Student>(
      `/api/v1/students/${id}`,
      data,
    );
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/students/${id}`);
  },
};
