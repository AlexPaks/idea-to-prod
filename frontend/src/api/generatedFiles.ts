import { apiRequest } from "./client";
import type {
  GeneratedFileContent,
  GeneratedFileMetadata,
} from "../types/generatedFile";

export const generatedFilesApi = {
  listByRunId(runId: string): Promise<GeneratedFileMetadata[]> {
    return apiRequest<GeneratedFileMetadata[]>(`/api/runs/${runId}/files`);
  },

  getContent(runId: string, path: string): Promise<GeneratedFileContent> {
    const query = new URLSearchParams({ path }).toString();
    return apiRequest<GeneratedFileContent>(`/api/runs/${runId}/files/content?${query}`);
  },
};
