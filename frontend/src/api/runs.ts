import { apiRequest } from "./client";
import type { WorkflowRun } from "../types/workflowRun";

export const runsApi = {
  startForProject(projectId: string): Promise<WorkflowRun> {
    return apiRequest<WorkflowRun>(`/api/projects/${projectId}/runs`, {
      method: "POST",
    });
  },

  getById(runId: string): Promise<WorkflowRun> {
    return apiRequest<WorkflowRun>(`/api/runs/${runId}`);
  },

  listForProject(projectId: string): Promise<WorkflowRun[]> {
    return apiRequest<WorkflowRun[]>(`/api/projects/${projectId}/runs`);
  },
};
