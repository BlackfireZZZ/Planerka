import { apiClient } from "./client";

export interface ClassGroup {
  id: string;
  institution_id: string;
  name: string;
  student_count: number;
  created_at: string;
  updated_at: string;
}

export interface ClassGroupCreate {
  name: string;
  student_count: number;
}

export interface ClassGroupUpdate {
  name?: string;
  student_count?: number;
}

export const classGroupsApi = {
  create: async (
    institutionId: string,
    data: ClassGroupCreate,
  ): Promise<ClassGroup> => {
    const response = await apiClient.post<ClassGroup>(
      `/api/v1/class-groups?institution_id=${institutionId}`,
      data,
    );
    return response.data;
  },

  list: async (institutionId: string): Promise<ClassGroup[]> => {
    const response = await apiClient.get<ClassGroup[]>(
      `/api/v1/class-groups?institution_id=${institutionId}`,
    );
    return response.data;
  },

  get: async (id: string): Promise<ClassGroup> => {
    const response = await apiClient.get<ClassGroup>(
      `/api/v1/class-groups/${id}`,
    );
    return response.data;
  },

  update: async (id: string, data: ClassGroupUpdate): Promise<ClassGroup> => {
    const response = await apiClient.put<ClassGroup>(
      `/api/v1/class-groups/${id}`,
      data,
    );
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/class-groups/${id}`);
  },
};
