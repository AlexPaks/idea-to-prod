export type JiraConnectionPayload = {
  enabled: boolean;
  server_url: string;
  tool_name: string;
  timeout_seconds: number;
  arguments_template_json: string;
  project_key: string;
};

export type JiraConnectionConfig = JiraConnectionPayload & {
  updated_at: string | null;
};

export type JiraConnectionTestResult = {
  ok: boolean;
  message: string;
  tool_name: string | null;
  argument_keys: string[];
  available_tools: string[];
};
