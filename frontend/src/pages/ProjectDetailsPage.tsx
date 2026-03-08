import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { projectsApi } from "../api/projects";
import { runsApi } from "../api/runs";
import type { Project } from "../types/project";
import type { WorkflowRun } from "../types/workflowRun";

export function ProjectDetailsPage() {
  const navigate = useNavigate();
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isStarting, setIsStarting] = useState(false);
  const [isDeletingProject, setIsDeletingProject] = useState(false);
  const [deletingRunId, setDeletingRunId] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!projectId) {
      setError("Missing project id.");
      setIsLoading(false);
      return;
    }

    const loadDetails = async () => {
      setError("");
      setIsLoading(true);

      try {
        const [projectData, runData] = await Promise.all([
          projectsApi.getById(projectId),
          runsApi.listForProject(projectId),
        ]);
        setProject(projectData);
        setRuns(runData);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown error";
        setError(message);
      } finally {
        setIsLoading(false);
      }
    };

    loadDetails();
  }, [projectId]);

  const onStartGeneration = async () => {
    if (!projectId) {
      return;
    }

    setIsStarting(true);
    setError("");

    try {
      const run = await runsApi.startForProject(projectId);
      navigate(`/runs/${run.id}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
    } finally {
      setIsStarting(false);
    }
  };

  const onDeleteProject = async () => {
    if (!projectId || !project) {
      return;
    }

    const shouldDelete = window.confirm(
      `Delete project "${project.name}" and all related runs/artifacts?`
    );
    if (!shouldDelete) {
      return;
    }

    setIsDeletingProject(true);
    setError("");

    try {
      await projectsApi.deleteById(projectId);
      navigate("/projects");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
    } finally {
      setIsDeletingProject(false);
    }
  };

  const onDeleteRun = async (runId: string) => {
    const shouldDelete = window.confirm(
      `Delete run "${runId}" and all related artifacts?`
    );
    if (!shouldDelete) {
      return;
    }

    setDeletingRunId(runId);
    setError("");

    try {
      await runsApi.deleteById(runId);
      setRuns((current) => current.filter((run) => run.id !== runId));
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
    } finally {
      setDeletingRunId(null);
    }
  };

  if (isLoading) {
    return <p>Loading project details...</p>;
  }

  if (error) {
    return <p className="error">Failed to load project: {error}</p>;
  }

  if (!project) {
    return <p className="muted">Project not found.</p>;
  }

  return (
    <section className="stack">
      <div className="row">
        <h2>{project.name}</h2>
        <Link to="/projects">Back to projects</Link>
      </div>

      <div className="card stack">
        <p>
          <strong>ID:</strong> {project.id}
        </p>
        <p>
          <strong>Status:</strong> {project.status}
        </p>
        <p>
          <strong>Created:</strong>{" "}
          {new Date(project.created_at).toLocaleString()}
        </p>
        <p>
          <strong>Idea:</strong> {project.idea}
        </p>
      </div>

      <button type="button" className="button" disabled={isStarting} onClick={onStartGeneration}>
        {isStarting ? "Starting..." : "Start Generation"}
      </button>
      <button
        type="button"
        className="button button-danger"
        disabled={isDeletingProject}
        onClick={onDeleteProject}
      >
        {isDeletingProject ? "Deleting Project..." : "Delete Project"}
      </button>

      <section className="stack">
        <h3>Workflow Runs</h3>
        {runs.length === 0 ? (
          <p className="muted">No runs yet.</p>
        ) : (
          <ul className="cards">
            {runs.map((run) => (
              <li key={run.id} className="card">
                <p>
                  <strong>Run:</strong> {run.id}
                </p>
                <p>
                  <strong>Status:</strong> {run.status}
                </p>
                <p>
                  <strong>Current Step:</strong> {run.current_step ?? "-"}
                </p>
                <div className="row-actions">
                  <Link to={`/runs/${run.id}`}>View run details</Link>
                  <button
                    type="button"
                    className="button button-danger"
                    disabled={deletingRunId === run.id}
                    onClick={() => onDeleteRun(run.id)}
                  >
                    {deletingRunId === run.id ? "Deleting..." : "Delete Run"}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </section>
  );
}
