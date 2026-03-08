export type WorkflowRunStatus = "queued" | "running" | "completed" | "failed";
export type WorkflowStepStatus = "pending" | "in_progress" | "completed" | "failed";
export type WorkflowStepName =
  | "intake"
  | "high_level_design"
  | "detailed_design"
  | "code_generation"
  | "test_generation"
  | "test_execution"
  | "completed";

export type WorkflowStep = {
  name: WorkflowStepName;
  status: WorkflowStepStatus;
  started_at: string | null;
  completed_at: string | null;
};

export type WorkflowRun = {
  id: string;
  project_id: string;
  status: WorkflowRunStatus;
  current_step: WorkflowStepName | null;
  steps: WorkflowStep[];
  created_at: string;
  updated_at: string;
  artifacts: string[];
  execution_event_ids: string[];
};
