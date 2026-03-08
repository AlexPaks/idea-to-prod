import { apiRequest } from "./client";
import type { Artifact } from "../types/artifact";

export const artifactsApi = {
  listByRunId(runId: string): Promise<Artifact[]> {
    return apiRequest<Artifact[]>(`/api/runs/${runId}/artifacts`);
  },

  getById(artifactId: string): Promise<Artifact> {
    return apiRequest<Artifact>(`/api/artifacts/${artifactId}`);
  },
};
