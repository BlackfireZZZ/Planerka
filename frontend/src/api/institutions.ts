import { apiClient } from "./client";

export interface Institution {
  id: string;
  name: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface InstitutionCreate {
  name: string;
}

export interface InstitutionUpdate {
  name?: string;
}

export const institutionsApi = {
  create: async (data: InstitutionCreate): Promise<Institution> => {
    const response = await apiClient.post<Institution>(
      "/api/v1/institutions",
      data,
    );
    return response.data;
  },

  list: async (): Promise<Institution[]> => {
    const response = await apiClient.get<Institution[]>("/api/v1/institutions");
    return response.data;
  },

  get: async (id: string): Promise<Institution> => {
    const response = await apiClient.get<Institution>(
      `/api/v1/institutions/${id}`,
    );
    return response.data;
  },

  update: async (id: string, data: InstitutionUpdate): Promise<Institution> => {
    const response = await apiClient.put<Institution>(
      `/api/v1/institutions/${id}`,
      data,
    );
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/institutions/${id}`);
  },
};
