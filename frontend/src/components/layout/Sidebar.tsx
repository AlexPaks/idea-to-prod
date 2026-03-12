import { ProjectTree } from "../projects/ProjectTree";
import type { Project, UserProfile } from "../../types/dashboard";

type SidebarProps = {
  user: UserProfile;
  projects: Project[];
  selectedProjectId: string;
  onSelectProject: (projectId: string) => void;
  onCreateProject?: () => void;
  onOpenSettings?: () => void;
};

export function Sidebar({
  user,
  projects,
  selectedProjectId,
  onSelectProject,
  onCreateProject,
  onOpenSettings,
}: SidebarProps) {
  return (
    <div className="flex h-full flex-col rounded-3xl border border-slate-200 bg-slate-50 p-5 shadow-card">
      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <div className="flex items-center gap-3">
          <img
            src={user.avatar}
            alt={user.name}
            className="h-12 w-12 rounded-full border border-slate-200 object-cover"
          />
          <div>
            <p className="text-sm font-semibold text-slate-900">{user.name}</p>
            <p className="text-xs text-slate-500">{user.email}</p>
            <p className="mt-1 text-[11px] font-medium text-slate-400">{user.role}</p>
          </div>
        </div>
      </div>

      <button
        type="button"
        onClick={onCreateProject}
        className="mt-4 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
      >
        Create Project
      </button>

      <div className="mt-5 min-h-0 flex-1 overflow-y-auto pr-1">
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
          Project Tree
        </h3>
        <ProjectTree
          projects={projects}
          selectedProjectId={selectedProjectId}
          onSelectProject={onSelectProject}
        />
      </div>

      <button
        type="button"
        onClick={onOpenSettings}
        className="mt-4 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-left transition hover:border-slate-300"
      >
        <p className="text-sm font-semibold text-slate-900">Settings</p>
        <p className="mt-1 text-xs text-slate-500">Open integrations configuration</p>
      </button>
    </div>
  );
}
