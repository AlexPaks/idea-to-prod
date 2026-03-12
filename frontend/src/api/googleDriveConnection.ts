import { apiRequest } from "./client";
import type {
  GoogleDriveConnectionConfig,
  GoogleDriveConnectionPayload,
  GoogleDriveConnectionTestResult,
} from "../types/googleDriveConnection";

export const googleDriveConnectionApi = {
  get(): Promise<GoogleDriveConnectionConfig> {
    return apiRequest<GoogleDriveConnectionConfig>("/api/settings/google-drive");
  },

  save(payload: GoogleDriveConnectionPayload): Promise<GoogleDriveConnectionConfig> {
    return apiRequest<GoogleDriveConnectionConfig>("/api/settings/google-drive", {
      method: "PUT",
      body: payload,
    });
  },

  test(payload: GoogleDriveConnectionPayload): Promise<GoogleDriveConnectionTestResult> {
    return apiRequest<GoogleDriveConnectionTestResult>("/api/settings/google-drive/test", {
      method: "POST",
      body: payload,
    });
  },
};
