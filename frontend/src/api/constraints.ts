import { apiClient } from "./client";

export interface Constraint {
  id: string;
  institution_id: string;
  constraint_type: string;
  constraint_data: Record<string, unknown>;
  priority: number;
  created_at: string;
  updated_at: string;
}

export interface ConstraintCreate {
  constraint_type: string;
  constraint_data: Record<string, unknown>;
  priority?: number;
}

export interface ConstraintUpdate {
  constraint_type?: string;
  constraint_data?: Record<string, unknown>;
  priority?: number;
}

export const constraintsApi = {
  create: async (
    institutionId: string,
    data: ConstraintCreate,
  ): Promise<Constraint> => {
    const response = await apiClient.post<Constraint>(
      `/api/v1/constraints?institution_id=${institutionId}`,
      data,
    );
    return response.data;
  },

  list: async (institutionId: string): Promise<Constraint[]> => {
    const response = await apiClient.get<Constraint[]>(
      `/api/v1/constraints?institution_id=${institutionId}`,
    );
    return response.data;
  },

  get: async (id: string): Promise<Constraint> => {
    const response = await apiClient.get<Constraint>(
      `/api/v1/constraints/${id}`,
    );
    return response.data;
  },

  update: async (id: string, data: ConstraintUpdate): Promise<Constraint> => {
    const response = await apiClient.put<Constraint>(
      `/api/v1/constraints/${id}`,
      data,
    );
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/constraints/${id}`);
  },
};
