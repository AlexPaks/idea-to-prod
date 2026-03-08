import { apiRequest } from "./client";
import type { CreateProjectPayload, Project } from "../types/project";

export const projectsApi = {
  create(payload: CreateProjectPayload): Promise<Project> {
    return apiRequest<Project>("/api/projects", {
      method: "POST",
      body: payload,
    });
  },

  list(): Promise<Project[]> {
    return apiRequest<Project[]>("/api/projects");
  },

  getById(projectId: string): Promise<Project> {
    return apiRequest<Project>(`/api/projects/${projectId}`);
  },

  deleteById(projectId: string): Promise<void> {
    return apiRequest<void>(`/api/projects/${projectId}`, {
      method: "DELETE",
    });
  },
};
