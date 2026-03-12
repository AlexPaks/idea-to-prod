import { apiRequest } from "./client";
import type {
  GitHubConnectionConfig,
  GitHubConnectionPayload,
  GitHubConnectionTestResult,
} from "../types/githubConnection";

export const githubConnectionApi = {
  get(): Promise<GitHubConnectionConfig> {
    return apiRequest<GitHubConnectionConfig>("/api/settings/github");
  },

  save(payload: GitHubConnectionPayload): Promise<GitHubConnectionConfig> {
    return apiRequest<GitHubConnectionConfig>("/api/settings/github", {
      method: "PUT",
      body: payload,
    });
  },

  test(payload: GitHubConnectionPayload): Promise<GitHubConnectionTestResult> {
    return apiRequest<GitHubConnectionTestResult>("/api/settings/github/test", {
      method: "POST",
      body: payload,
    });
  },
};
