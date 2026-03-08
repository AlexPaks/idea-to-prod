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
type LiveConnectionState = "connecting" | "connected" | "disconnected";

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

    let isClosed = false;
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

        setLiveConnectionState("disconnected");
        reconnectTimer = window.setTimeout(connect, WS_RECONNECT_DELAY_MS);
      };
    };

    connect();

    return () => {
      isClosed = true;
      if (reconnectTimer !== undefined) {
        window.clearTimeout(reconnectTimer);
      }
      if (socket && socket.readyState <= WebSocket.OPEN) {
        socket.close();
      }
    };
  }, [runId]);

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
    return <p>Loading run details...</p>;
  }

  if (error) {
    return <p className="error">Failed to load run: {error}</p>;
  }

  if (!run) {
    return <p className="muted">Run not found.</p>;
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
      navigate(`/projects/${run.project_id}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
      setIsDeletingRun(false);
    }
  };

  return (
    <section className="stack">
      <div className="row">
        <h2>Run Details</h2>
        <div className="row-actions">
          <Link to={`/projects/${run.project_id}`}>Back to project</Link>
          <button
            type="button"
            className="button button-danger"
            disabled={isDeletingRun}
            onClick={onDeleteRun}
          >
            {isDeletingRun ? "Deleting..." : "Delete Run"}
          </button>
        </div>
      </div>

      <div className="card stack">
        <p>
          <strong>Run ID:</strong> {run.id}
        </p>
        <p>
          <strong>Project ID:</strong> {run.project_id}
        </p>
        <p>
          <strong>Overall Status:</strong> {run.status}
        </p>
        <p>
          <strong>Current Step:</strong> {run.current_step ?? "-"}
        </p>
        <p>
          <strong>Updated:</strong> {new Date(run.updated_at).toLocaleString()}
        </p>
        <p>
          <strong>Live Updates:</strong>{" "}
          <span className={liveConnectionState === "connected" ? "ok" : "muted"}>
            {liveConnectionState === "connected"
              ? "connected"
              : `${liveConnectionState} (polling fallback active)`}
          </span>
        </p>
      </div>

      <section className="stack">
        <h3>Step Timeline</h3>
        <ul className="timeline">
          {run.steps.map((step) => (
            <li key={step.name} className="timeline-item">
              <span className={`step-badge step-${step.status}`}>{labelForStatus(step.status)}</span>
              <div className="stack">
                <p>
                  <strong>{step.name}</strong>
                </p>
                <p className="muted">
                  Started: {formatDate(step.started_at)} | Completed: {formatDate(step.completed_at)}
                </p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="stack">
        <h3>Test Results</h3>
        {run.test_result ? (
          <div className="card stack">
            <div className="row">
              <span
                className={`step-badge ${
                  run.test_result.status === "passed" ? "step-completed" : "step-failed"
                }`}
              >
                {run.test_result.status}
              </span>
              <span className="muted">
                {new Date(run.test_result.executed_at).toLocaleString()}
              </span>
            </div>
            <p>
              <strong>Summary:</strong> {run.test_result.summary}
            </p>
            <p>
              <strong>Exit Code:</strong> {run.test_result.exit_code}
            </p>
            <details>
              <summary>stdout</summary>
              <pre className="code-viewer">{run.test_result.stdout || "(empty)"}</pre>
            </details>
            <details>
              <summary>stderr</summary>
              <pre className="code-viewer">{run.test_result.stderr || "(empty)"}</pre>
            </details>
          </div>
        ) : (
          <p className="muted">No real test results recorded yet.</p>
        )}
      </section>

      <section className="stack">
        <h3>Artifacts</h3>
        {artifacts.length === 0 ? (
          <p className="muted">No artifacts generated yet.</p>
        ) : (
          <div className="artifact-layout">
            <div className="artifact-list">
              {artifacts.map((artifact) => (
                <button
                  key={artifact.id}
                  type="button"
                  className={`artifact-tab${artifact.id === selectedArtifactId ? " artifact-tab-active" : ""}`}
                  onClick={() => setSelectedArtifactId(artifact.id)}
                >
                  <strong>{artifact.title}</strong>
                  <span className="muted">{prettifyArtifactType(artifact.artifact_type)}</span>
                </button>
              ))}
            </div>
            <div className="artifact-panel">
              {selectedArtifact ? (
                <div className="stack">
                  <div className="row">
                    <h4>{selectedArtifact.title}</h4>
                    <span className="muted">
                      {new Date(selectedArtifact.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="muted">
                    Type: {prettifyArtifactType(selectedArtifact.artifact_type)}
                  </p>
                  <pre className="artifact-content">{selectedArtifact.content}</pre>
                </div>
              ) : (
                <p className="muted">Select an artifact to view details.</p>
              )}
            </div>
          </div>
        )}
      </section>

      <section className="stack">
        <h3>Generated Files</h3>
        {generatedFiles.length === 0 ? (
          <p className="muted">No generated files available yet.</p>
        ) : (
          <div className="generated-files-layout">
            <div className="generated-file-list">
              {generatedFiles.map((file) => (
                <button
                  key={file.artifact_id}
                  type="button"
                  className={`generated-file-item${
                    file.path === selectedFilePath ? " generated-file-item-active" : ""
                  }`}
                  onClick={() => setSelectedFilePath(file.path)}
                >
                  <strong>{file.path}</strong>
                  <span className="muted">
                    {formatBytes(file.size_bytes)} | {new Date(file.updated_at).toLocaleString()}
                  </span>
                </button>
              ))}
            </div>
            <div className="generated-file-panel">
              {isFileLoading ? (
                <p>Loading file...</p>
              ) : fileError ? (
                <p className="error">Failed to load file: {fileError}</p>
              ) : selectedFileContent ? (
                <div className="stack">
                  <div className="row">
                    <h4>{selectedFileContent.path}</h4>
                    <span className="muted">{selectedFileContent.language ?? "plain text"}</span>
                  </div>
                  <pre className="code-viewer">{selectedFileContent.content}</pre>
                </div>
              ) : (
                <p className="muted">Select a generated file to view content.</p>
              )}
            </div>
          </div>
        )}
      </section>
    </section>
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
