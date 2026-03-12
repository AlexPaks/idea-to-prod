export type GitHubConnectionPayload = {
  enabled: boolean;
  server_url: string;
  tool_name: string;
  timeout_seconds: number;
  arguments_template_json: string;
  owner: string;
  repository: string;
};

export type GitHubConnectionConfig = GitHubConnectionPayload & {
  updated_at: string | null;
};

export type GitHubConnectionTestResult = {
  ok: boolean;
  message: string;
  tool_name: string | null;
  argument_keys: string[];
  available_tools: string[];
};
