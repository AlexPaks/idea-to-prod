export type GoogleDriveConnectionPayload = {
  enabled: boolean;
  server_url: string;
  tool_name: string;
  read_tool_name: string;
  folder_id: string;
  timeout_seconds: number;
  arguments_template_json: string;
  read_arguments_template_json: string;
};

export type GoogleDriveConnectionConfig = GoogleDriveConnectionPayload & {
  updated_at: string | null;
};

export type GoogleDriveConnectionTestResult = {
  ok: boolean;
  message: string;
  create_tool_name: string | null;
  create_argument_keys: string[];
  read_tool_name: string | null;
  read_argument_keys: string[];
};
