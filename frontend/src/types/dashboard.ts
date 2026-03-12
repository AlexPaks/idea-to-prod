export type IntegrationStatus = "connected" | "pending" | "not_connected";

export type Integration = {
  id: string;
  name: string;
  status: IntegrationStatus;
  description: string;
};

export type ProjectNavItemType = "runs" | "artifacts" | "repo" | "deployment";

export type ProjectNavItem = {
  id: string;
  label: string;
  type: ProjectNavItemType;
  count?: number;
};

export type RunStatus = "running" | "completed" | "failed" | "queued";

export type RunItem = {
  id: string;
  name: string;
  status: RunStatus;
  currentStep: string | null;
  createdAt: string;
  updatedAt: string;
  artifactsCount: number;
};

export type ArtifactItem = {
  id: string;
  title: string;
  type: "high_level_design" | "detailed_design" | "code_summary" | "test_summary" | "test_result" | "generated_file";
  createdAt: string;
};

export type Project = {
  id: string;
  name: string;
  description: string;
  status: "draft" | "in_progress" | "completed";
  createdAt: string;
  stats: {
    runs: number;
    successRate: string;
    artifacts: number;
    completedRuns: number;
  };
  children: ProjectNavItem[];
  runs: RunItem[];
  artifacts: ArtifactItem[];
  integrations: Integration[];
  selectedRunId: string | null;
};

export type UserProfile = {
  name: string;
  email: string;
  avatar: string;
  role: string;
};
