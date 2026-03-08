import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { runsApi } from "../api/runs";
import type { WorkflowRun, WorkflowStepStatus } from "../types/workflowRun";

const POLL_INTERVAL_MS = 2500;

export function RunDetailsPage() {
  const { runId } = useParams<{ runId: string }>();
  const [run, setRun] = useState<WorkflowRun | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!runId) {
      setError("Missing run id.");
      setIsLoading(false);
      return;
    }

    let isMounted = true;

    const loadRun = async () => {
      try {
        const data = await runsApi.getById(runId);
        if (isMounted) {
          setRun(data);
          setError("");
          setIsLoading(false);
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown error";
        if (isMounted) {
          setError(message);
          setIsLoading(false);
        }
      }
    };

    void loadRun();
    const intervalId = window.setInterval(() => {
      void loadRun();
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
