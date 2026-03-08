export type ArtifactType =
  | "high_level_design"
  | "detailed_design"
  | "code_summary"
  | "test_summary"
  | "generated_file";

export type Artifact = {
  id: string;
  run_id: string;
  project_id: string;
  artifact_type: ArtifactType;
  title: string;
  content: string;
  created_at: string;
  metadata?: Record<string, unknown>;
};
