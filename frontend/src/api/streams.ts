import { apiClient } from "./client";

export interface Stream {
  id: string;
  institution_id: string;
  name: string;
  created_at: string;
  updated_at: string;
  class_groups: Array<{ id: string; name: string }>;
}

export interface StreamCreate {
  name: string;
  class_group_ids?: string[];
}

export interface StreamUpdate {
  name?: string;
  class_group_ids?: string[];
}

export const streamsApi = {
  create: async (
    institutionId: string,
    data: StreamCreate,
  ): Promise<Stream> => {
    const response = await apiClient.post<Stream>(
      `/api/v1/streams?institution_id=${institutionId}`,
      data,
    );
    return response.data;
  },

  list: async (institutionId: string): Promise<Stream[]> => {
    const response = await apiClient.get<Stream[]>(
      `/api/v1/streams?institution_id=${institutionId}`,
    );
    return response.data;
  },

  get: async (id: string): Promise<Stream> => {
    const response = await apiClient.get<Stream>(`/api/v1/streams/${id}`);
    return response.data;
  },

  update: async (id: string, data: StreamUpdate): Promise<Stream> => {
    const response = await apiClient.put<Stream>(`/api/v1/streams/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/streams/${id}`);
  },
};
