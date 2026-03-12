import type { RunItem } from "../../types/dashboard";

type RunListProps = {
  runs: RunItem[];
  selectedRunId?: string | null;
  onSelectRun?: (runId: string) => void;
  onOpenRun?: (runId: string) => void;
};

const runStatusStyles: Record<RunItem["status"], string> = {
  completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
  failed: "bg-rose-50 text-rose-700 border-rose-200",
  running: "bg-blue-50 text-blue-700 border-blue-200",
  queued: "bg-slate-100 text-slate-600 border-slate-200",
};

export function RunList({
  runs,
  selectedRunId = null,
  onSelectRun,
  onOpenRun,
}: RunListProps) {
  if (runs.length === 0) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-900">Recent Runs</h3>
        </div>
        <p className="text-sm text-slate-500">No runs yet. Start your first workflow run.</p>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900">Recent Runs</h3>
        <p className="text-xs text-slate-500">{runs.length} total</p>
      </div>

      <div className="space-y-3">
        {runs.map((run) => (
          <article
            key={run.id}
            className={`rounded-xl border px-4 py-3 ${
              selectedRunId === run.id
                ? "border-slate-900 bg-slate-900 text-white"
                : "border-slate-200 bg-slate-50"
            }`}
          >
            <div className="flex items-start justify-between gap-4">
              <button
                type="button"
                onClick={() => onSelectRun?.(run.id)}
                className="text-left"
              >
                <p
                  className={`text-sm font-semibold ${
                    selectedRunId === run.id ? "text-white" : "text-slate-900"
                  }`}
                >
                  {run.name}
                </p>
                <p
                  className={`mt-1 text-xs ${
                    selectedRunId === run.id ? "text-slate-300" : "text-slate-500"
                  }`}
                >
                  {run.id} | Step: {run.currentStep ?? "-"} | Artifacts: {run.artifactsCount}
                </p>
              </button>
              <div className="flex items-center gap-2">
                <span
                  className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold ${
                    runStatusStyles[run.status]
                  }`}
                >
                  {run.status}
                </span>
                <button
                  type="button"
                  onClick={() => onOpenRun?.(run.id)}
                  className="rounded-lg border border-slate-300 px-2 py-1 text-[11px] font-semibold text-slate-700 transition hover:border-slate-500 hover:text-slate-900"
                >
                  Open
                </button>
              </div>
            </div>

            <div
              className={`mt-2 flex items-center gap-4 text-xs ${
                selectedRunId === run.id ? "text-slate-300" : "text-slate-500"
              }`}
            >
              <span>Created: {run.createdAt}</span>
              <span>Updated: {run.updatedAt}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
