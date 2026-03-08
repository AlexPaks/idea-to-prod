import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { projectsApi } from "../api/projects";
import type { Project } from "../types/project";

export function ProjectsListPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadProjects = async () => {
      setIsLoading(true);
      setError("");

      try {
        const data = await projectsApi.list();
        setProjects(data);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown error";
        setError(message);
      } finally {
        setIsLoading(false);
      }
    };

    loadProjects();
  }, []);

  if (isLoading) {
    return <p>Loading projects...</p>;
  }

  if (error) {
    return <p className="error">Failed to load projects: {error}</p>;
  }

  return (
    <section className="stack">
      <div className="row">
        <h2>Projects</h2>
        <Link className="button" to="/projects/new">
          Create Project
        </Link>
      </div>

      {projects.length === 0 ? (
        <p className="muted">No projects yet. Create your first project.</p>
      ) : (
        <ul className="cards">
          {projects.map((project) => (
            <li key={project.id} className="card">
              <h3>{project.name}</h3>
              <p>{project.idea}</p>
              <p className="meta">
                Status: {project.status} -{" "}
                {new Date(project.created_at).toLocaleString()}
              </p>
              <Link to={`/projects/${project.id}`}>View details</Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
