import type { Project } from "../../types/dashboard";

type TopHeaderProps = {
  project: Project;
  onNewRun?: () => void;
  onViewLatestRun?: () => void;
  canViewLatestRun?: boolean;
  isStartingRun?: boolean;
};

export function TopHeader({
  project,
  onNewRun,
  onViewLatestRun,
  canViewLatestRun = false,
  isStartingRun = false,
}: TopHeaderProps) {
  return (
    <header className="rounded-3xl border border-slate-200 bg-white px-6 py-5 shadow-card">
      <div className="flex items-start justify-between gap-6">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
            Project Overview
          </p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950">
            {project.name}
          </h1>
          <p className="mt-2 max-w-3xl text-sm text-slate-600">{project.description}</p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onViewLatestRun}
            disabled={!canViewLatestRun}
            className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:text-slate-900 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400"
          >
            Open Latest Run
          </button>
          <button
            type="button"
            onClick={onNewRun}
            disabled={isStartingRun}
            className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            {isStartingRun ? "Starting..." : "New Run"}
          </button>
        </div>
      </div>
    </header>
  );
}
