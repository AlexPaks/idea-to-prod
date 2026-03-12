import type { Project } from "../../types/dashboard";

type ProjectDetailsProps = {
  project: Project;
};

export function ProjectDetails({ project }: ProjectDetailsProps) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
      <h3 className="text-sm font-semibold text-slate-900">Project Details</h3>
      <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-4 text-sm">
        <div>
          <dt className="text-xs uppercase tracking-[0.1em] text-slate-500">Project ID</dt>
          <dd className="mt-1 font-medium text-slate-900">{project.id}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-[0.1em] text-slate-500">Status</dt>
          <dd className="mt-1 font-medium capitalize text-slate-900">{project.status}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-[0.1em] text-slate-500">Created</dt>
          <dd className="mt-1 font-medium text-slate-900">{project.createdAt}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-[0.1em] text-slate-500">Selected Run</dt>
          <dd className="mt-1 font-medium text-slate-900">{project.selectedRunId ?? "-"}</dd>
        </div>
      </dl>
    </section>
  );
}
