import type { Project } from "../../types/dashboard";

type ProjectTreeProps = {
  projects: Project[];
  selectedProjectId: string;
  onSelectProject: (projectId: string) => void;
};

export function ProjectTree({
  projects,
  selectedProjectId,
  onSelectProject,
}: ProjectTreeProps) {
  return (
    <div className="space-y-2">
      {projects.map((project) => {
        const isActive = project.id === selectedProjectId;

        return (
          <div
            key={project.id}
            className={`rounded-xl border p-3 transition ${
              isActive
                ? "border-slate-900 bg-slate-900 text-white"
                : "border-slate-200 bg-white text-slate-900 hover:border-slate-300"
            }`}
          >
            <button
              type="button"
              onClick={() => onSelectProject(project.id)}
              className="w-full text-left"
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-semibold">{project.name}</p>
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.08em] ${
                    isActive ? "bg-white/15 text-white" : statusStyle[project.status]
                  }`}
                >
                  {formatStatus(project.status)}
                </span>
              </div>
              <p className={`mt-1 text-xs ${isActive ? "text-slate-300" : "text-slate-500"}`}>
                {summarizeDescription(project.description)}
              </p>
            </button>
          </div>
        );
      })}
    </div>
  );
}

const statusStyle = {
  draft: "bg-slate-100 text-slate-600",
  in_progress: "bg-amber-100 text-amber-700",
  completed: "bg-emerald-100 text-emerald-700",
} as const;

function formatStatus(status: Project["status"]): string {
  if (status === "in_progress") {
    return "In Progress";
  }
  if (status === "completed") {
    return "Completed";
  }
  return "Draft";
}

function summarizeDescription(value: string): string {
  const normalized = value.trim().replace(/\s+/g, " ");
  if (!normalized) {
    return "No description";
  }
  if (normalized.length <= 72) {
    return normalized;
  }
  return `${normalized.slice(0, 69)}...`;
}
