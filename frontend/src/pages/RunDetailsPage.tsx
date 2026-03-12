import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { artifactsApi } from "../api/artifacts";
import { generatedFilesApi } from "../api/generatedFiles";
import { createRunUpdatesSocket, isRunUpdatedMessage } from "../api/runUpdates";
import { runsApi } from "../api/runs";
import type { Artifact } from "../types/artifact";
import type {
  GeneratedFileContent,
  GeneratedFileMetadata,
} from "../types/generatedFile";
import type {
  WorkflowRun,
  WorkflowStepStatus,
} from "../types/workflowRun";

const POLL_INTERVAL_MS = 2500;
const WS_RECONNECT_DELAY_MS = 3000;
type LiveConnectionState = "connecting" | "connected" | "disconnected" | "inactive";

export function RunDetailsPage() {
  const navigate = useNavigate();
  const { runId } = useParams<{ runId: string }>();
  const [run, setRun] = useState<WorkflowRun | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [generatedFiles, setGeneratedFiles] = useState<GeneratedFileMetadata[]>([]);
  const [selectedArtifactId, setSelectedArtifactId] = useState<string | null>(null);
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null);
  const [selectedFileContent, setSelectedFileContent] = useState<GeneratedFileContent | null>(
    null
  );
  const [isFileLoading, setIsFileLoading] = useState(false);
  const [fileError, setFileError] = useState("");
  const [liveConnectionState, setLiveConnectionState] = useState<LiveConnectionState>("connecting");
  const [isLoading, setIsLoading] = useState(true);
  const [isDeletingRun, setIsDeletingRun] = useState(false);
  const [error, setError] = useState("");
  const trackedArtifactsCountRef = useRef(0);

  const selectedArtifact = useMemo(
    () => artifacts.find((artifact) => artifact.id === selectedArtifactId) ?? null,
    [artifacts, selectedArtifactId]
  );

  useEffect(() => {
    trackedArtifactsCountRef.current = run?.artifacts.length ?? 0;
  }, [run?.artifacts.length]);

  useEffect(() => {
    if (!runId) {
      setError("Missing run id.");
      setIsLoading(false);
      return;
    }

    let isMounted = true;

    const applyArtifacts = (artifactData: Artifact[]) => {
      setArtifacts(artifactData);
      setSelectedArtifactId((current) => {
        if (artifactData.length === 0) {
          return null;
        }
        if (current && artifactData.some((artifact) => artifact.id === current)) {
          return current;
        }
        return artifactData[0].id;
      });
    };

    const applyGeneratedFiles = (files: GeneratedFileMetadata[]) => {
      setGeneratedFiles(files);
      setSelectedFilePath((current) => {
        if (files.length === 0) {
          return null;
        }
        if (current && files.some((item) => item.path === current)) {
          return current;
        }
        return files[0].path;
      });
    };

    const loadRunData = async () => {
      try {
        const [runData, artifactData, generatedFileData] = await Promise.all([
          runsApi.getById(runId),
          artifactsApi.listByRunId(runId),
          generatedFilesApi.listByRunId(runId),
        ]);

        if (!isMounted) {
          return;
        }

        setRun(runData);
        applyArtifacts(artifactData);
        applyGeneratedFiles(generatedFileData);
        setError("");
        setIsLoading(false);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown error";
        if (isMounted) {
          setError(message);
          setIsLoading(false);
        }
      }
    };

    void loadRunData();
    const intervalId = window.setInterval(() => {
      void loadRunData();
    }, POLL_INTERVAL_MS);

    return () => {
      isMounted = false;
      window.clearInterval(intervalId);
    };
  }, [runId]);

  useEffect(() => {
    if (!runId) {
      setLiveConnectionState("disconnected");
      return;
    }
    if (!isRunLiveUpdatable(run?.status)) {
      setLiveConnectionState(run ? "inactive" : "connecting");
      return;
    }

    let isClosed = false;
    let shouldReconnect = true;
    let reconnectTimer: number | undefined;
    let socket: WebSocket | null = null;

    const refreshRunAssets = async () => {
      try {
        const [artifactData, generatedFileData] = await Promise.all([
          artifactsApi.listByRunId(runId),
          generatedFilesApi.listByRunId(runId),
        ]);

        if (!isClosed) {
          setArtifacts(artifactData);
          setSelectedArtifactId((current) => {
            if (artifactData.length === 0) {
              return null;
            }
            if (current && artifactData.some((item) => item.id === current)) {
              return current;
            }
            return artifactData[0].id;
          });

          setGeneratedFiles(generatedFileData);
          setSelectedFilePath((current) => {
            if (generatedFileData.length === 0) {
              return null;
            }
            if (current && generatedFileData.some((item) => item.path === current)) {
              return current;
            }
            return generatedFileData[0].path;
          });
        }
      } catch {
        // Polling remains active and will reconcile state shortly.
      }
    };

    const connect = () => {
      if (isClosed) {
        return;
      }

      setLiveConnectionState("connecting");
      socket = createRunUpdatesSocket(runId);

      socket.onopen = () => {
        if (!isClosed) {
          setLiveConnectionState("connected");
        }
      };

      socket.onmessage = (event) => {
        if (isClosed) {
          return;
        }

        try {
          const parsed: unknown = JSON.parse(event.data);
          if (!isRunUpdatedMessage(parsed) || parsed.run.id !== runId) {
            return;
          }

          setRun(parsed.run);
          setError("");

          if (!isRunLiveUpdatable(parsed.run.status)) {
            shouldReconnect = false;
            setLiveConnectionState("inactive");
            if (socket && socket.readyState <= WebSocket.OPEN) {
              socket.close();
            }
            return;
          }

          if (parsed.run.artifacts.length !== trackedArtifactsCountRef.current) {
            void refreshRunAssets();
          }
        } catch {
          // Ignore malformed payloads.
        }
      };

      socket.onerror = () => {
        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.close();
        }
      };

      socket.onclose = () => {
        if (isClosed) {
          return;
        }
        if (!shouldReconnect) {
          setLiveConnectionState("inactive");
          return;
        }

        setLiveConnectionState("disconnected");
        reconnectTimer = window.setTimeout(connect, WS_RECONNECT_DELAY_MS);
      };
    };

    connect();

    return () => {
      isClosed = true;
      shouldReconnect = false;
      if (reconnectTimer !== undefined) {
        window.clearTimeout(reconnectTimer);
      }
      if (socket && socket.readyState <= WebSocket.OPEN) {
        socket.close();
      }
    };
  }, [runId, run?.status]);

  useEffect(() => {
    if (!runId || !selectedFilePath) {
      setSelectedFileContent(null);
      setFileError("");
      return;
    }

    let isMounted = true;

    const loadFileContent = async () => {
      setIsFileLoading(true);
      setFileError("");
      try {
        const content = await generatedFilesApi.getContent(runId, selectedFilePath);
        if (isMounted) {
          setSelectedFileContent(content);
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown error";
        if (isMounted) {
          setFileError(message);
          setSelectedFileContent(null);
        }
      } finally {
        if (isMounted) {
          setIsFileLoading(false);
        }
      }
    };

    void loadFileContent();

    return () => {
      isMounted = false;
    };
  }, [runId, selectedFilePath]);

  if (isLoading) {
    return <p className="p-8 text-slate-600">Loading run details...</p>;
  }

  if (error) {
    return (
      <div className="p-8">
        <p className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          Failed to load run: {error}
        </p>
      </div>
    );
  }

  if (!run) {
    return <p className="p-8 text-slate-600">Run not found.</p>;
  }

  const onDeleteRun = async () => {
    const shouldDelete = window.confirm(
      `Delete run "${run.id}" and all related artifacts?`
    );
    if (!shouldDelete) {
      return;
    }

    setIsDeletingRun(true);
    setError("");

    try {
      await runsApi.deleteById(run.id);
      navigate("/");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
      setIsDeletingRun(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-100 px-6 py-8">
      <section className="mx-auto max-w-[1500px] space-y-5">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
              Workflow Run
            </p>
            <h1 className="mt-1 text-2xl font-bold text-slate-950">Run Details</h1>
          </div>
          <div className="flex items-center gap-2">
            <Link
              to="/"
              className="rounded-xl border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:text-slate-900"
            >
              Back to Dashboard
            </Link>
            <Link
              to="/settings/integrations"
              className="rounded-xl border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:text-slate-900"
            >
              Integration Settings
            </Link>
          </div>
        </div>

        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="space-y-2">
              <p className="text-sm text-slate-600">
                <span className="font-semibold text-slate-900">Run ID:</span> {run.id}
              </p>
              <p className="text-sm text-slate-600">
                <span className="font-semibold text-slate-900">Project ID:</span> {run.project_id}
              </p>
              <p className="text-sm text-slate-600">
                <span className="font-semibold text-slate-900">Current Step:</span>{" "}
                {run.current_step ?? "-"}
              </p>
              <p className="text-sm text-slate-600">
                <span className="font-semibold text-slate-900">Updated:</span>{" "}
                {new Date(run.updated_at).toLocaleString()}
              </p>
            </div>
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium uppercase tracking-[0.1em] text-slate-500">
                  Status
                </span>
                <span className={statusPillClass(run.status)}>{run.status}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium uppercase tracking-[0.1em] text-slate-500">
                  Live Updates
                </span>
                <span className={liveStatusPillClass(liveConnectionState)}>
                  {liveConnectionState === "connected" && "connected"}
                  {liveConnectionState === "inactive" && "inactive (run finished)"}
                  {liveConnectionState === "connecting" && "connecting"}
                  {liveConnectionState === "disconnected" && "disconnected"}
                </span>
              </div>
              <button
                type="button"
                className="rounded-xl bg-rose-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-rose-700 disabled:cursor-not-allowed disabled:bg-rose-300"
                disabled={isDeletingRun}
                onClick={onDeleteRun}
              >
                {isDeletingRun ? "Deleting..." : "Delete Run"}
              </button>
            </div>
          </div>
        </section>

        <section className="grid grid-cols-1 gap-4 xl:grid-cols-12">
          <div className="xl:col-span-7">
            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
              <h2 className="text-sm font-semibold text-slate-900">Step Timeline</h2>
              <ul className="mt-4 space-y-3">
                {run.steps.map((step) => (
                  <li
                    key={step.name}
                    className="flex items-start justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
                  >
                    <div>
                      <p className="text-sm font-semibold capitalize text-slate-900">
                        {step.name.split("_").join(" ")}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">
                        Started: {formatDate(step.started_at)} | Completed:{" "}
                        {formatDate(step.completed_at)}
                      </p>
                    </div>
                    <span className={stepStatusPillClass(step.status)}>
                      {labelForStatus(step.status)}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          </div>
          <div className="xl:col-span-5">
            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
              <h2 className="text-sm font-semibold text-slate-900">Test Results</h2>
              {run.test_result ? (
                <div className="mt-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span
                      className={
                        run.test_result.status === "passed"
                          ? "rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-emerald-700"
                          : "rounded-full border border-rose-200 bg-rose-50 px-2.5 py-1 text-[11px] font-semibold text-rose-700"
                      }
                    >
                      {run.test_result.status}
                    </span>
                    <span className="text-xs text-slate-500">
                      {new Date(run.test_result.executed_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-sm text-slate-700">
                    <span className="font-semibold text-slate-900">Summary:</span>{" "}
                    {run.test_result.summary}
                  </p>
                  <p className="text-sm text-slate-700">
                    <span className="font-semibold text-slate-900">Exit Code:</span>{" "}
                    {run.test_result.exit_code}
                  </p>
                  <details className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                    <summary className="cursor-pointer text-sm font-semibold text-slate-800">
                      stdout
                    </summary>
                    <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap text-xs text-slate-700">
                      {run.test_result.stdout || "(empty)"}
                    </pre>
                  </details>
                  <details className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                    <summary className="cursor-pointer text-sm font-semibold text-slate-800">
                      stderr
                    </summary>
                    <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap text-xs text-slate-700">
                      {run.test_result.stderr || "(empty)"}
                    </pre>
                  </details>
                </div>
              ) : (
                <p className="mt-4 text-sm text-slate-500">No test results recorded yet.</p>
              )}
            </section>
          </div>
        </section>

        <section className="grid grid-cols-1 gap-4 xl:grid-cols-12">
          <div className="xl:col-span-6">
            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
              <h2 className="text-sm font-semibold text-slate-900">Artifacts</h2>
              {artifacts.length === 0 ? (
                <p className="mt-4 text-sm text-slate-500">No artifacts generated yet.</p>
              ) : (
                <div className="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-12">
                  <div className="space-y-2 lg:col-span-5">
                    {artifacts.map((artifact) => (
                      <button
                        key={artifact.id}
                        type="button"
                        className={`w-full rounded-xl border px-3 py-2 text-left transition ${
                          artifact.id === selectedArtifactId
                            ? "border-slate-900 bg-slate-900 text-white"
                            : "border-slate-200 bg-slate-50 text-slate-900 hover:border-slate-300"
                        }`}
                        onClick={() => setSelectedArtifactId(artifact.id)}
                      >
                        <p className="text-sm font-semibold">{artifact.title}</p>
                        <p
                          className={`mt-1 text-xs ${
                            artifact.id === selectedArtifactId ? "text-slate-300" : "text-slate-500"
                          }`}
                        >
                          {prettifyArtifactType(artifact.artifact_type)}
                        </p>
                      </button>
                    ))}
                  </div>
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 lg:col-span-7">
                    {selectedArtifact ? (
                      <div className="space-y-2">
                        <div className="flex items-start justify-between gap-2">
                          <h3 className="text-sm font-semibold text-slate-900">
                            {selectedArtifact.title}
                          </h3>
                          <span className="text-xs text-slate-500">
                            {new Date(selectedArtifact.created_at).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500">
                          Type: {prettifyArtifactType(selectedArtifact.artifact_type)}
                        </p>
                        <pre className="max-h-[28rem] overflow-auto whitespace-pre-wrap rounded-lg border border-slate-200 bg-white p-3 text-xs text-slate-700">
                          {selectedArtifact.content}
                        </pre>
                      </div>
                    ) : (
                      <p className="text-sm text-slate-500">Select an artifact to view details.</p>
                    )}
                  </div>
                </div>
              )}
            </section>
          </div>
          <div className="xl:col-span-6">
            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
              <h2 className="text-sm font-semibold text-slate-900">Generated Files</h2>
              {generatedFiles.length === 0 ? (
                <p className="mt-4 text-sm text-slate-500">No generated files available yet.</p>
              ) : (
                <div className="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-12">
                  <div className="space-y-2 lg:col-span-5">
                    {generatedFiles.map((file) => (
                      <button
                        key={file.artifact_id}
                        type="button"
                        className={`w-full rounded-xl border px-3 py-2 text-left transition ${
                          file.path === selectedFilePath
                            ? "border-slate-900 bg-slate-900 text-white"
                            : "border-slate-200 bg-slate-50 text-slate-900 hover:border-slate-300"
                        }`}
                        onClick={() => setSelectedFilePath(file.path)}
                      >
                        <p className="truncate text-sm font-semibold">{file.path}</p>
                        <p
                          className={`mt-1 text-xs ${
                            file.path === selectedFilePath ? "text-slate-300" : "text-slate-500"
                          }`}
                        >
                          {formatBytes(file.size_bytes)} | {new Date(file.updated_at).toLocaleString()}
                        </p>
                      </button>
                    ))}
                  </div>
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 lg:col-span-7">
                    {isFileLoading ? (
                      <p className="text-sm text-slate-500">Loading file...</p>
                    ) : fileError ? (
                      <p className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
                        Failed to load file: {fileError}
                      </p>
                    ) : selectedFileContent ? (
                      <div className="space-y-2">
                        <div className="flex items-start justify-between gap-2">
                          <h3 className="text-sm font-semibold text-slate-900">
                            {selectedFileContent.path}
                          </h3>
                          <span className="text-xs text-slate-500">
                            {selectedFileContent.language ?? "plain text"}
                          </span>
                        </div>
                        <pre className="max-h-[28rem] overflow-auto whitespace-pre-wrap rounded-lg border border-slate-200 bg-white p-3 text-xs text-slate-700">
                          {selectedFileContent.content}
                        </pre>
                      </div>
                    ) : (
                      <p className="text-sm text-slate-500">Select a generated file to view content.</p>
                    )}
                  </div>
                </div>
              )}
            </section>
          </div>
        </section>
      </section>
    </main>
  );
}

function formatDate(value: string | null): string {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString();
}

function formatBytes(value: number): string {
  if (value < 1024) {
    return `${value} B`;
  }
  const kb = value / 1024;
  return `${kb.toFixed(1)} KB`;
}

function labelForStatus(status: WorkflowStepStatus): string {
  if (status === "in_progress") {
    return "in progress";
  }
  return status;
}

function prettifyArtifactType(value: string): string {
  return value.split("_").join(" ");
}

function isRunLiveUpdatable(status: WorkflowRun["status"] | undefined): boolean {
  return status === "queued" || status === "running";
}

function statusPillClass(status: WorkflowRun["status"]): string {
  if (status === "completed") {
    return "rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-emerald-700";
  }
  if (status === "failed") {
    return "rounded-full border border-rose-200 bg-rose-50 px-2.5 py-1 text-[11px] font-semibold text-rose-700";
  }
  if (status === "running") {
    return "rounded-full border border-blue-200 bg-blue-50 px-2.5 py-1 text-[11px] font-semibold text-blue-700";
  }
  return "rounded-full border border-slate-200 bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600";
}

function stepStatusPillClass(status: WorkflowStepStatus): string {
  if (status === "completed") {
    return "rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-emerald-700";
  }
  if (status === "failed") {
    return "rounded-full border border-rose-200 bg-rose-50 px-2.5 py-1 text-[11px] font-semibold text-rose-700";
  }
  if (status === "in_progress") {
    return "rounded-full border border-blue-200 bg-blue-50 px-2.5 py-1 text-[11px] font-semibold text-blue-700";
  }
  return "rounded-full border border-slate-200 bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600";
}

function liveStatusPillClass(state: LiveConnectionState): string {
  if (state === "connected") {
    return "rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-emerald-700";
  }
  if (state === "inactive") {
    return "rounded-full border border-slate-200 bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600";
  }
  if (state === "connecting") {
    return "rounded-full border border-blue-200 bg-blue-50 px-2.5 py-1 text-[11px] font-semibold text-blue-700";
  }
  return "rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-[11px] font-semibold text-amber-700";
}
