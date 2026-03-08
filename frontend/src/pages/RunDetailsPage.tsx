import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { artifactsApi } from "../api/artifacts";
import { runsApi } from "../api/runs";
import type { Artifact } from "../types/artifact";
import type { WorkflowRun, WorkflowStepStatus } from "../types/workflowRun";

const POLL_INTERVAL_MS = 2500;

export function RunDetailsPage() {
  const { runId } = useParams<{ runId: string }>();
  const [run, setRun] = useState<WorkflowRun | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [selectedArtifactId, setSelectedArtifactId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const selectedArtifact = useMemo(
    () => artifacts.find((artifact) => artifact.id === selectedArtifactId) ?? null,
    [artifacts, selectedArtifactId]
  );

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

  if (isLoading) {
    return <p>Loading run details...</p>;
  }

  if (error) {
    return <p className="error">Failed to load run: {error}</p>;
  }

  if (!run) {
    return <p className="muted">Run not found.</p>;
  }

  return (
    <section className="stack">
      <div className="row">
        <h2>Run Details</h2>
        <Link to={`/projects/${run.project_id}`}>Back to project</Link>
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
