import type { WorkflowRun } from "../types/workflowRun";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type RunUpdatedMessage = {
  type: "run.updated";
  run: WorkflowRun;
};

export function createRunUpdatesSocket(runId: string): WebSocket {
  const url = new URL(API_BASE_URL);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = `/ws/runs/${runId}`;
  url.search = "";
  url.hash = "";
  return new WebSocket(url.toString());
}

export function isRunUpdatedMessage(value: unknown): value is RunUpdatedMessage {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const record = value as Record<string, unknown>;
  return record.type === "run.updated" && typeof record.run === "object" && record.run !== null;
}
