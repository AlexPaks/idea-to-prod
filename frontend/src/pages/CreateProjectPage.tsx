import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { projectsApi } from "../api/projects";

export function CreateProjectPage() {
  const navigate = useNavigate();
  const [idea, setIdea] = useState("");
  const [name, setName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const project = await projectsApi.create({
        idea,
        name: name.trim() ? name.trim() : undefined,
      });
      navigate(`/projects/${project.id}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="stack">
      <h2>Create Project</h2>

      <form className="stack form" onSubmit={onSubmit}>
        <label className="stack">
          <span>Idea *</span>
          <textarea
            value={idea}
            onChange={(event) => setIdea(event.target.value)}
            required
            rows={5}
            placeholder="Describe your product idea"
          />
        </label>

        <label className="stack">
          <span>Name (optional)</span>
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Leave empty to auto-generate"
          />
        </label>

        {error && <p className="error">Failed to create project: {error}</p>}

        <button className="button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Creating..." : "Create Project"}
        </button>
      </form>
    </section>
  );
}
