import type { Integration, IntegrationStatus } from "../../types/dashboard";

type IntegrationSettingsCardProps = {
  integration: Integration;
  compact?: boolean;
};

const statusStyles: Record<IntegrationStatus, string> = {
  connected: "bg-emerald-50 text-emerald-700 border-emerald-200",
  pending: "bg-amber-50 text-amber-700 border-amber-200",
  not_connected: "bg-slate-100 text-slate-600 border-slate-200",
};

const statusLabel: Record<IntegrationStatus, string> = {
  connected: "Connected",
  pending: "Pending",
  not_connected: "Not Connected",
};

export function IntegrationSettingsCard({
  integration,
  compact = false,
}: IntegrationSettingsCardProps) {
  return (
    <article
      className={`rounded-2xl border border-slate-200 bg-white ${
        compact ? "p-3" : "p-4"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h4 className="text-sm font-semibold text-slate-900">{integration.name}</h4>
          <p className="mt-1 text-xs text-slate-500">{integration.description}</p>
        </div>
        <span
          className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold ${
            statusStyles[integration.status]
          }`}
        >
          {statusLabel[integration.status]}
        </span>
      </div>
    </article>
  );
}
