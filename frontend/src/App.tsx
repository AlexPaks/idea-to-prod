import { Link, Navigate, Route, Routes } from "react-router-dom";

import { CreateProjectPage } from "./pages/CreateProjectPage";
import { ProjectDetailsPage } from "./pages/ProjectDetailsPage";
import { ProjectsListPage } from "./pages/ProjectsListPage";
import { RunDetailsPage } from "./pages/RunDetailsPage";

export default function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>IdeaToProd</h1>
        <nav>
          <Link to="/projects">Projects</Link>
          <Link to="/projects/new">New Project</Link>
        </nav>
      </header>

      <main className="page">
        <Routes>
          <Route path="/" element={<Navigate to="/projects" replace />} />
          <Route path="/projects" element={<ProjectsListPage />} />
          <Route path="/projects/new" element={<CreateProjectPage />} />
          <Route path="/projects/:projectId" element={<ProjectDetailsPage />} />
          <Route path="/runs/:runId" element={<RunDetailsPage />} />
          <Route path="*" element={<p>Page not found.</p>} />
        </Routes>
      </main>
    </div>
  );
}
