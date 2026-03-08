export type GeneratedFileMetadata = {
  path: string;
  artifact_id: string;
  size_bytes: number;
  language: string | null;
  updated_at: string;
};

export type GeneratedFileContent = {
  path: string;
  content: string;
  language: string | null;
};
