export type ProjectStatus = "draft" | "in_progress" | "completed";

export type Project = {
  id: string;
  name: string;
  idea: string;
  status: ProjectStatus;
  created_at: string;
};

export type CreateProjectPayload = {
  idea: string;
  name?: string;
};
