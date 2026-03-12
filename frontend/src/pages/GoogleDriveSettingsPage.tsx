import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { githubConnectionApi } from "../api/githubConnection";
import { googleDriveConnectionApi } from "../api/googleDriveConnection";
import { jiraConnectionApi } from "../api/jiraConnection";
import type {
  GitHubConnectionPayload,
  GitHubConnectionTestResult,
} from "../types/githubConnection";
import type {
  GoogleDriveConnectionPayload,
  GoogleDriveConnectionTestResult,
} from "../types/googleDriveConnection";
import type {
  JiraConnectionPayload,
  JiraConnectionTestResult,
} from "../types/jiraConnection";

const DEFAULT_GOOGLE: GoogleDriveConnectionPayload = {
  enabled: false,
  server_url: "",
  tool_name: "create_document",
  read_tool_name: "get_document",
  folder_id: "",
  timeout_seconds: 30,
  arguments_template_json: "",
  read_arguments_template_json: "",
};

const DEFAULT_GITHUB: GitHubConnectionPayload = {
  enabled: false,
  server_url: "",
  tool_name: "github",
  timeout_seconds: 30,
  arguments_template_json: "",
  owner: "",
  repository: "",
};

const DEFAULT_JIRA: JiraConnectionPayload = {
  enabled: false,
  server_url: "",
  tool_name: "jira",
  timeout_seconds: 30,
  arguments_template_json: "",
  project_key: "",
};

export function IntegrationsSettingsPage() {
  const [google, setGoogle] = useState<GoogleDriveConnectionPayload>(DEFAULT_GOOGLE);
  const [github, setGithub] = useState<GitHubConnectionPayload>(DEFAULT_GITHUB);
  const [jira, setJira] = useState<JiraConnectionPayload>(DEFAULT_JIRA);

  const [googleUpdatedAt, setGoogleUpdatedAt] = useState<string | null>(null);
  const [githubUpdatedAt, setGithubUpdatedAt] = useState<string | null>(null);
  const [jiraUpdatedAt, setJiraUpdatedAt] = useState<string | null>(null);

  const [googleResult, setGoogleResult] = useState<GoogleDriveConnectionTestResult | null>(
    null
  );
  const [githubResult, setGithubResult] = useState<GitHubConnectionTestResult | null>(null);
  const [jiraResult, setJiraResult] = useState<JiraConnectionTestResult | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isSavingGoogle, setIsSavingGoogle] = useState(false);
  const [isSavingGithub, setIsSavingGithub] = useState(false);
  const [isSavingJira, setIsSavingJira] = useState(false);
  const [isTestingGoogle, setIsTestingGoogle] = useState(false);
  const [isTestingGithub, setIsTestingGithub] = useState(false);
  const [isTestingJira, setIsTestingJira] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    let isMounted = true;
    const load = async () => {
      try {
        const [googleConfig, githubConfig, jiraConfig] = await Promise.all([
          googleDriveConnectionApi.get(),
          githubConnectionApi.get(),
          jiraConnectionApi.get(),
        ]);
        if (!isMounted) {
          return;
        }
        setGoogle({
          enabled: googleConfig.enabled,
          server_url: googleConfig.server_url,
          tool_name: googleConfig.tool_name,
          read_tool_name: googleConfig.read_tool_name,
          folder_id: googleConfig.folder_id,
          timeout_seconds: googleConfig.timeout_seconds,
          arguments_template_json: googleConfig.arguments_template_json,
          read_arguments_template_json: googleConfig.read_arguments_template_json,
        });
        setGoogleUpdatedAt(googleConfig.updated_at);

        setGithub({
          enabled: githubConfig.enabled,
          server_url: githubConfig.server_url,
          tool_name: githubConfig.tool_name,
          timeout_seconds: githubConfig.timeout_seconds,
          arguments_template_json: githubConfig.arguments_template_json,
          owner: githubConfig.owner,
          repository: githubConfig.repository,
        });
        setGithubUpdatedAt(githubConfig.updated_at);

        setJira({
          enabled: jiraConfig.enabled,
          server_url: jiraConfig.server_url,
          tool_name: jiraConfig.tool_name,
          timeout_seconds: jiraConfig.timeout_seconds,
          arguments_template_json: jiraConfig.arguments_template_json,
          project_key: jiraConfig.project_key,
        });
        setJiraUpdatedAt(jiraConfig.updated_at);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown error";
        if (isMounted) {
          setError(message);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };
    void load();
    return () => {
      isMounted = false;
    };
  }, []);

  const saveGoogle = async () => {
    setIsSavingGoogle(true);
    setError("");
    setMessage("");
    try {
      const saved = await googleDriveConnectionApi.save(google);
      setGoogleUpdatedAt(saved.updated_at);
      setMessage("Google Drive settings saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsSavingGoogle(false);
    }
  };

  const testGoogle = async () => {
    setIsTestingGoogle(true);
    setGoogleResult(null);
    setError("");
    try {
      const result = await googleDriveConnectionApi.test(google);
      setGoogleResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsTestingGoogle(false);
    }
  };

  const saveGithub = async () => {
    setIsSavingGithub(true);
    setError("");
    setMessage("");
    try {
      const saved = await githubConnectionApi.save(github);
      setGithubUpdatedAt(saved.updated_at);
      setMessage("GitHub settings saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsSavingGithub(false);
    }
  };

  const testGithub = async () => {
    setIsTestingGithub(true);
    setGithubResult(null);
    setError("");
    try {
      const result = await githubConnectionApi.test(github);
      setGithubResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsTestingGithub(false);
    }
  };

  const saveJira = async () => {
    setIsSavingJira(true);
    setError("");
    setMessage("");
    try {
      const saved = await jiraConnectionApi.save(jira);
      setJiraUpdatedAt(saved.updated_at);
      setMessage("Jira settings saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsSavingJira(false);
    }
  };

  const testJira = async () => {
    setIsTestingJira(true);
    setJiraResult(null);
    setError("");
    try {
      const result = await jiraConnectionApi.test(jira);
      setJiraResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsTestingJira(false);
    }
  };

  if (isLoading) {
    return <p className="p-8 text-slate-600">Loading integration settings...</p>;
  }

  return (
    <main className="min-h-screen bg-slate-100 px-6 py-8">
      <section className="mx-auto max-w-6xl space-y-5">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Integration Settings</h1>
            <p className="mt-1 text-sm text-slate-600">
              Configure MCP servers used by workflow and repository-related actions.
            </p>
          </div>
          <Link
            to="/"
            className="rounded-xl border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:text-slate-900"
          >
            Back to Dashboard
          </Link>
        </div>

        {error && (
          <p className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-700">
            {error}
          </p>
        )}
        {message && (
          <p className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-700">
            {message}
          </p>
        )}

        <section className="grid grid-cols-1 gap-4 xl:grid-cols-3">
          <article className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-card">
            <h2 className="text-sm font-semibold text-slate-900">Google Drive</h2>
            <ToggleRow
              label="Enabled"
              checked={google.enabled}
              onChange={(checked) => setGoogle((current) => ({ ...current, enabled: checked }))}
            />
            <InputRow
              label="Server URL"
              value={google.server_url}
              onChange={(value) => setGoogle((current) => ({ ...current, server_url: value }))}
              placeholder="http://localhost:3001/mcp"
            />
            <InputRow
              label="Create Tool"
              value={google.tool_name}
              onChange={(value) => setGoogle((current) => ({ ...current, tool_name: value }))}
              placeholder="create_document"
            />
            <InputRow
              label="Read Tool"
              value={google.read_tool_name}
              onChange={(value) =>
                setGoogle((current) => ({ ...current, read_tool_name: value }))
              }
              placeholder="get_document"
            />
            <InputRow
              label="Folder ID"
              value={google.folder_id}
              onChange={(value) => setGoogle((current) => ({ ...current, folder_id: value }))}
              placeholder="optional"
            />
            <InputRow
              label="Timeout"
              value={String(google.timeout_seconds)}
              onChange={(value) =>
                setGoogle((current) => ({
                  ...current,
                  timeout_seconds: Number(value) || 1,
                }))
              }
              placeholder="30"
            />
            <TextAreaRow
              label="Create Args Template"
              value={google.arguments_template_json}
              onChange={(value) =>
                setGoogle((current) => ({ ...current, arguments_template_json: value }))
              }
              placeholder='{"title":"{title}","content":"{content}"}'
            />
            <TextAreaRow
              label="Read Args Template"
              value={google.read_arguments_template_json}
              onChange={(value) =>
                setGoogle((current) => ({ ...current, read_arguments_template_json: value }))
              }
              placeholder='{"document_id":"{document_id}"}'
            />
            <ActionsRow
              onTest={testGoogle}
              onSave={saveGoogle}
              isTesting={isTestingGoogle}
              isSaving={isSavingGoogle}
              updatedAt={googleUpdatedAt}
            />
            {googleResult && (
              <ResultPanel ok={googleResult.ok} message={googleResult.message} />
            )}
          </article>

          <article className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-card">
            <h2 className="text-sm font-semibold text-slate-900">GitHub</h2>
            <ToggleRow
              label="Enabled"
              checked={github.enabled}
              onChange={(checked) => setGithub((current) => ({ ...current, enabled: checked }))}
            />
            <InputRow
              label="Server URL"
              value={github.server_url}
              onChange={(value) => setGithub((current) => ({ ...current, server_url: value }))}
              placeholder="http://localhost:3002/mcp"
            />
            <InputRow
              label="Tool Name"
              value={github.tool_name}
              onChange={(value) =>
                setGithub((current) => ({ ...current, tool_name: value }))
              }
              placeholder="github"
            />
            <InputRow
              label="Owner"
              value={github.owner}
              onChange={(value) => setGithub((current) => ({ ...current, owner: value }))}
              placeholder="org-or-user"
            />
            <InputRow
              label="Repository"
              value={github.repository}
              onChange={(value) => setGithub((current) => ({ ...current, repository: value }))}
              placeholder="repo-name"
            />
            <InputRow
              label="Timeout"
              value={String(github.timeout_seconds)}
              onChange={(value) =>
                setGithub((current) => ({
                  ...current,
                  timeout_seconds: Number(value) || 1,
                }))
              }
              placeholder="30"
            />
            <TextAreaRow
              label="Args Template"
              value={github.arguments_template_json}
              onChange={(value) =>
                setGithub((current) => ({ ...current, arguments_template_json: value }))
              }
              placeholder='{"owner":"{owner}","repo":"{repository}"}'
            />
            <ActionsRow
              onTest={testGithub}
              onSave={saveGithub}
              isTesting={isTestingGithub}
              isSaving={isSavingGithub}
              updatedAt={githubUpdatedAt}
            />
            {githubResult && (
              <ResultPanel
                ok={githubResult.ok}
                message={
                  formatProbeMessage(
                    githubResult.message,
                    githubResult.tool_name,
                    githubResult.argument_keys
                  )
                }
              />
            )}
          </article>

          <article className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-card">
            <h2 className="text-sm font-semibold text-slate-900">Jira</h2>
            <ToggleRow
              label="Enabled"
              checked={jira.enabled}
              onChange={(checked) => setJira((current) => ({ ...current, enabled: checked }))}
            />
            <InputRow
              label="Server URL"
              value={jira.server_url}
              onChange={(value) => setJira((current) => ({ ...current, server_url: value }))}
              placeholder="http://localhost:3003/mcp"
            />
            <InputRow
              label="Tool Name"
              value={jira.tool_name}
              onChange={(value) => setJira((current) => ({ ...current, tool_name: value }))}
              placeholder="jira"
            />
            <InputRow
              label="Project Key"
              value={jira.project_key}
              onChange={(value) => setJira((current) => ({ ...current, project_key: value }))}
              placeholder="PROJ"
            />
            <InputRow
              label="Timeout"
              value={String(jira.timeout_seconds)}
              onChange={(value) =>
                setJira((current) => ({
                  ...current,
                  timeout_seconds: Number(value) || 1,
                }))
              }
              placeholder="30"
            />
            <TextAreaRow
              label="Args Template"
              value={jira.arguments_template_json}
              onChange={(value) =>
                setJira((current) => ({ ...current, arguments_template_json: value }))
              }
              placeholder='{"projectKey":"{project_key}"}'
            />
            <ActionsRow
              onTest={testJira}
              onSave={saveJira}
              isTesting={isTestingJira}
              isSaving={isSavingJira}
              updatedAt={jiraUpdatedAt}
            />
            {jiraResult && (
              <ResultPanel
                ok={jiraResult.ok}
                message={
                  formatProbeMessage(
                    jiraResult.message,
                    jiraResult.tool_name,
                    jiraResult.argument_keys
                  )
                }
              />
            )}
          </article>
        </section>
      </section>
    </main>
  );
}

type InputRowProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
};

function InputRow({ label, value, onChange, placeholder }: InputRowProps) {
  return (
    <label className="block space-y-1">
      <span className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">
        {label}
      </span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-slate-500"
      />
    </label>
  );
}

type TextAreaRowProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
};

function TextAreaRow({ label, value, onChange, placeholder }: TextAreaRowProps) {
  return (
    <label className="block space-y-1">
      <span className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">
        {label}
      </span>
      <textarea
        rows={3}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-slate-500"
      />
    </label>
  );
}

type ToggleRowProps = {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
};

function ToggleRow({ label, checked, onChange }: ToggleRowProps) {
  return (
    <label className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
      <span className="text-sm font-medium text-slate-700">{label}</span>
      <input
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
        className="h-4 w-4 accent-slate-900"
      />
    </label>
  );
}

type ActionsRowProps = {
  onTest: () => void;
  onSave: () => void;
  isTesting: boolean;
  isSaving: boolean;
  updatedAt: string | null;
};

function ActionsRow({
  onTest,
  onSave,
  isTesting,
  isSaving,
  updatedAt,
}: ActionsRowProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onTest}
          disabled={isTesting}
          className="rounded-xl border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-500 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400"
        >
          {isTesting ? "Testing..." : "Test"}
        </button>
        <button
          type="button"
          onClick={onSave}
          disabled={isSaving}
          className="rounded-xl bg-slate-900 px-3 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
        >
          {isSaving ? "Saving..." : "Save"}
        </button>
      </div>
      {updatedAt && <p className="text-xs text-slate-500">Saved: {new Date(updatedAt).toLocaleString()}</p>}
    </div>
  );
}

type ResultPanelProps = {
  ok: boolean;
  message: string;
};

function ResultPanel({ ok, message }: ResultPanelProps) {
  return (
    <p
      className={`rounded-xl border px-3 py-2 text-sm ${
        ok
          ? "border-emerald-200 bg-emerald-50 text-emerald-700"
          : "border-rose-200 bg-rose-50 text-rose-700"
      }`}
    >
      {message}
    </p>
  );
}

function formatProbeMessage(
  baseMessage: string,
  toolName: string | null,
  argumentKeys: string[]
): string {
  const details: string[] = [];
  if (toolName) {
    details.push(`tool: ${toolName}`);
  }
  if (argumentKeys.length > 0) {
    details.push(`args: ${argumentKeys.join(", ")}`);
  }

  if (details.length === 0) {
    return baseMessage;
  }
  return `${baseMessage} (${details.join(" | ")})`;
}
