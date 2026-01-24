import { apiClient } from "./client";

export interface Room {
  id: string;
  institution_id: string;
  name: string;
  capacity: number;
  room_type: string | null;
  equipment: string | null;
  created_at: string;
  updated_at: string;
}

export interface RoomCreate {
  name: string;
  capacity: number;
  room_type?: string;
  equipment?: string;
}

export interface RoomUpdate {
  name?: string;
  capacity?: number;
  room_type?: string;
  equipment?: string;
}

export const roomsApi = {
  create: async (institutionId: string, data: RoomCreate): Promise<Room> => {
    const response = await apiClient.post<Room>(
      `/api/v1/rooms?institution_id=${institutionId}`,
      data,
    );
    return response.data;
  },

  list: async (institutionId: string): Promise<Room[]> => {
    const response = await apiClient.get<Room[]>(
      `/api/v1/rooms?institution_id=${institutionId}`,
    );
    return response.data;
  },

  get: async (id: string): Promise<Room> => {
    const response = await apiClient.get<Room>(`/api/v1/rooms/${id}`);
    return response.data;
  },

  update: async (id: string, data: RoomUpdate): Promise<Room> => {
    const response = await apiClient.put<Room>(`/api/v1/rooms/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/rooms/${id}`);
  },
};
