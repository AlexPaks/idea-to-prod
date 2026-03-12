import { apiRequest } from "./client";
import type {
  JiraConnectionConfig,
  JiraConnectionPayload,
  JiraConnectionTestResult,
} from "../types/jiraConnection";

export const jiraConnectionApi = {
  get(): Promise<JiraConnectionConfig> {
    return apiRequest<JiraConnectionConfig>("/api/settings/jira");
  },

  save(payload: JiraConnectionPayload): Promise<JiraConnectionConfig> {
    return apiRequest<JiraConnectionConfig>("/api/settings/jira", {
      method: "PUT",
      body: payload,
    });
  },

  test(payload: JiraConnectionPayload): Promise<JiraConnectionTestResult> {
    return apiRequest<JiraConnectionTestResult>("/api/settings/jira/test", {
      method: "POST",
      body: payload,
    });
  },
};
