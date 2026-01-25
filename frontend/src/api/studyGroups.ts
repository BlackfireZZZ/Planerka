import { apiClient } from "./client";

export interface StudyGroup {
  id: string;
  institution_id: string;
  stream_id: string;
  name: string;
  created_at: string;
  updated_at: string;
  students: Array<{
    id: string;
    full_name: string;
    student_number: string | null;
  }>;
}

export interface StudyGroupCreate {
  stream_id: string;
  name: string;
  student_ids?: string[];
}

export interface StudyGroupUpdate {
  stream_id?: string;
  name?: string;
  student_ids?: string[];
}

export interface StudyGroupLessonLink {
  lesson_id: string;
  count: number;
}

export interface StudyGroupLessonAssignment {
  lesson_id: string;
  count: number;
}

export const studyGroupsApi = {
  create: async (
    institutionId: string,
    data: StudyGroupCreate,
  ): Promise<StudyGroup> => {
    const response = await apiClient.post<StudyGroup>(
      `/api/v1/study-groups?institution_id=${institutionId}`,
      data,
    );
    return response.data;
  },

  list: async (
    institutionId: string,
    streamId?: string,
  ): Promise<StudyGroup[]> => {
    const url = streamId
      ? `/api/v1/study-groups?institution_id=${institutionId}&stream_id=${streamId}`
      : `/api/v1/study-groups?institution_id=${institutionId}`;
    const response = await apiClient.get<StudyGroup[]>(url);
    return response.data;
  },

  get: async (id: string): Promise<StudyGroup> => {
    const response = await apiClient.get<StudyGroup>(
      `/api/v1/study-groups/${id}`,
    );
    return response.data;
  },

  update: async (id: string, data: StudyGroupUpdate): Promise<StudyGroup> => {
    const response = await apiClient.put<StudyGroup>(
      `/api/v1/study-groups/${id}`,
      data,
    );
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/study-groups/${id}`);
  },

  assignLessons: async (
    studyGroupId: string,
    items: StudyGroupLessonAssignment[],
  ): Promise<StudyGroupLessonLink[]> => {
    const response = await apiClient.post<StudyGroupLessonLink[]>(
      `/api/v1/study-groups/${studyGroupId}/assign-lessons`,
      { lessons: items },
    );
    return response.data;
  },

  getLessons: async (studyGroupId: string): Promise<StudyGroupLessonLink[]> => {
    const response = await apiClient.get<StudyGroupLessonLink[]>(
      `/api/v1/study-groups/${studyGroupId}/lessons`,
    );
    return response.data;
  },
};
