import type { ArtifactItem } from "../../types/dashboard";

type ArtifactListProps = {
  artifacts: ArtifactItem[];
};

const artifactTypeStyles: Record<ArtifactItem["type"], string> = {
  high_level_design: "bg-indigo-50 text-indigo-700",
  detailed_design: "bg-violet-50 text-violet-700",
  code_summary: "bg-sky-50 text-sky-700",
  test_summary: "bg-amber-50 text-amber-700",
  test_result: "bg-rose-50 text-rose-700",
  generated_file: "bg-emerald-50 text-emerald-700",
};

export function ArtifactList({ artifacts }: ArtifactListProps) {
  if (artifacts.length === 0) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-900">Artifacts</h3>
        </div>
        <p className="text-sm text-slate-500">No artifacts for the selected run yet.</p>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900">Artifacts</h3>
        <p className="text-xs text-slate-500">{artifacts.length} total</p>
      </div>

      <div className="space-y-3">
        {artifacts.map((artifact) => (
          <article
            key={artifact.id}
            className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-slate-900">{artifact.title}</p>
                <p className="mt-1 text-xs text-slate-500">
                  Created {artifact.createdAt}
                </p>
              </div>
              <span
                className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${
                  artifactTypeStyles[artifact.type]
                }`}
              >
                {artifact.type}
              </span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
