import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { artifactsApi } from "../api/artifacts";
import { createRunUpdatesSocket, isRunUpdatedMessage } from "../api/runUpdates";
import { runsApi } from "../api/runs";
import type { Artifact } from "../types/artifact";
import type { WorkflowRun, WorkflowStepStatus } from "../types/workflowRun";

const POLL_INTERVAL_MS = 2500;
const WS_RECONNECT_DELAY_MS = 3000;
type LiveConnectionState = "connecting" | "connected" | "disconnected";

export function RunDetailsPage() {
  const navigate = useNavigate();
  const { runId } = useParams<{ runId: string }>();
  const [run, setRun] = useState<WorkflowRun | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [selectedArtifactId, setSelectedArtifactId] = useState<string | null>(null);
  const [liveConnectionState, setLiveConnectionState] = useState<LiveConnectionState>("connecting");
  const [isLoading, setIsLoading] = useState(true);
  const [isDeletingRun, setIsDeletingRun] = useState(false);
  const [error, setError] = useState("");
  const artifactCountRef = useRef(0);

  const selectedArtifact = useMemo(
    () => artifacts.find((artifact) => artifact.id === selectedArtifactId) ?? null,
    [artifacts, selectedArtifactId]
  );

  useEffect(() => {
    artifactCountRef.current = artifacts.length;
  }, [artifacts.length]);

  useEffect(() => {
    if (!runId) {
      setError("Missing run id.");
      setIsLoading(false);
      return;
    }

    let isMounted = true;

    const loadRunData = async () => {
      try {
        const [runData, artifactData] = await Promise.all([
          runsApi.getById(runId),
          artifactsApi.listByRunId(runId),
        ]);

        if (!isMounted) {
          return;
        }

        setRun(runData);
        applyArtifacts(artifactData);

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

    const refreshArtifacts = async () => {
      try {
        const artifactData = await artifactsApi.listByRunId(runId);
        if (!isClosed) {
          applyArtifacts(artifactData);
        }
      } catch {
        // Polling still runs as a fallback. Swallow transient websocket-sync failures.
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

          if (parsed.run.artifacts.length !== artifactCountRef.current) {
            void refreshArtifacts();
          }
        } catch {
          // Ignore malformed websocket messages and keep polling fallback active.
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
    </section>
  );
}

function formatDate(value: string | null): string {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString();
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
