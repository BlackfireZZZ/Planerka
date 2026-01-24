import { apiClient } from "./client";

export interface TimeSlot {
  id: string;
  institution_id: string;
  day_of_week: number;
  start_time: string;
  end_time: string;
  slot_number: number;
  created_at: string;
  updated_at: string;
}

export interface TimeSlotCreate {
  day_of_week: number;
  start_time: string;
  end_time: string;
  slot_number: number;
}

export interface TimeSlotUpdate {
  day_of_week?: number;
  start_time?: string;
  end_time?: string;
  slot_number?: number;
}

export const timeSlotsApi = {
  create: async (
    institutionId: string,
    data: TimeSlotCreate,
  ): Promise<TimeSlot> => {
    const response = await apiClient.post<TimeSlot>(
      `/api/v1/time-slots?institution_id=${institutionId}`,
      data,
    );
    return response.data;
  },

  list: async (institutionId: string): Promise<TimeSlot[]> => {
    const response = await apiClient.get<TimeSlot[]>(
      `/api/v1/time-slots?institution_id=${institutionId}`,
    );
    return response.data;
  },

  get: async (id: string): Promise<TimeSlot> => {
    const response = await apiClient.get<TimeSlot>(`/api/v1/time-slots/${id}`);
    return response.data;
  },

  update: async (id: string, data: TimeSlotUpdate): Promise<TimeSlot> => {
    const response = await apiClient.put<TimeSlot>(
      `/api/v1/time-slots/${id}`,
      data,
    );
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/time-slots/${id}`);
  },
};
