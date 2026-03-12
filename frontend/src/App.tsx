import { Navigate, Route, Routes } from "react-router-dom";

import { DashboardPage } from "./pages/DashboardPage";
import { IntegrationsSettingsPage } from "./pages/GoogleDriveSettingsPage";
import { RunDetailsPage } from "./pages/RunDetailsPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/runs/:runId" element={<RunDetailsPage />} />
      <Route path="/settings/integrations" element={<IntegrationsSettingsPage />} />
      <Route path="/settings/google-drive" element={<Navigate to="/settings/integrations" replace />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
