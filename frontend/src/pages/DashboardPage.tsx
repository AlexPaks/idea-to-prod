import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { artifactsApi } from "../api/artifacts";
import { githubConnectionApi } from "../api/githubConnection";
import { googleDriveConnectionApi } from "../api/googleDriveConnection";
import { jiraConnectionApi } from "../api/jiraConnection";
import { projectsApi } from "../api/projects";
import { runsApi } from "../api/runs";
import { AppShell } from "../components/layout/AppShell";
import { Sidebar } from "../components/layout/Sidebar";
import { TopHeader } from "../components/layout/TopHeader";
import { ArtifactList } from "../components/artifacts/ArtifactList";
import { ProjectDetails } from "../components/projects/ProjectDetails";
import { RunList } from "../components/runs/RunList";
import { IntegrationSettingsCard } from "../components/settings/IntegrationSettingsCard";
import type { Artifact } from "../types/artifact";
import type { GitHubConnectionConfig } from "../types/githubConnection";
import type { JiraConnectionConfig } from "../types/jiraConnection";
import type { Project as ApiProject } from "../types/project";
import type { WorkflowRun } from "../types/workflowRun";
import type { GoogleDriveConnectionConfig } from "../types/googleDriveConnection";
import type {
  ArtifactItem,
  Integration,
  Project,
  RunItem,
  UserProfile,
} from "../types/dashboard";

const REFRESH_INTERVAL_MS = 5000;

const CURRENT_USER: UserProfile = {
  name: "IdeaToProd Operator",
  email: "operator@ideatoprod.local",
  avatar:
    "https://images.unsplash.com/photo-1599566150163-29194dcaad36?auto=format&fit=crop&w=200&q=80",
  role: "Workspace Admin",
};

export function DashboardPage() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<ApiProject[]>([]);
  const [runsByProject, setRunsByProject] = useState<Record<string, WorkflowRun[]>>({});
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [googleDriveConfig, setGoogleDriveConfig] = useState<GoogleDriveConnectionConfig | null>(
    null
  );
  const [githubConfig, setGithubConfig] = useState<GitHubConnectionConfig | null>(null);
  const [jiraConfig, setJiraConfig] = useState<JiraConnectionConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isStartingRun, setIsStartingRun] = useState(false);
  const [isCreatingProject, setIsCreatingProject] = useState(false);
  const [isCreateProjectOpen, setIsCreateProjectOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [newProjectIdea, setNewProjectIdea] = useState("");
  const [error, setError] = useState("");

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === selectedProjectId) ?? null,
    [projects, selectedProjectId]
  );

  const selectedProjectRuns = useMemo(
    () => runsByProject[selectedProjectId] ?? [],
    [runsByProject, selectedProjectId]
  );

  const integrations = useMemo(
    () => buildIntegrationsSummary(googleDriveConfig, githubConfig, jiraConfig),
    [googleDriveConfig, githubConfig, jiraConfig]
  );

  const loadWorkspaceData = useCallback(
    async (preferredProjectId?: string) => {
      setIsLoading(true);
      setError("");

      try {
        const [projectList, googleConfig, githubConnection, jiraConnection] = await Promise.all([
          projectsApi.list(),
          googleDriveConnectionApi.get().catch(() => null),
          githubConnectionApi.get().catch(() => null),
          jiraConnectionApi.get().catch(() => null),
        ]);

        const runEntries = await Promise.all(
          projectList.map(async (project) => {
            const projectRuns = await runsApi.listForProject(project.id);
            return [project.id, projectRuns] as const;
          })
        );

        const runMap = Object.fromEntries(runEntries);
        setProjects(projectList);
        setRunsByProject(runMap);
        setGoogleDriveConfig(googleConfig);
        setGithubConfig(githubConnection);
        setJiraConfig(jiraConnection);

        const nextProjectId = selectProjectId({
          projects: projectList,
          previousProjectId: selectedProjectId,
          preferredProjectId,
        });
        setSelectedProjectId(nextProjectId);

        const nextRuns = runMap[nextProjectId] ?? [];
        setSelectedRunId((current) =>
          current && nextRuns.some((run) => run.id === current) ? current : nextRuns[0]?.id ?? null
        );
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown error";
        setError(message);
      } finally {
        setIsLoading(false);
      }
    },
    [selectedProjectId]
  );

  const refreshRunsForProject = useCallback(
    async (projectId: string, preferredRunId?: string | null) => {
      const projectRuns = await runsApi.listForProject(projectId);
      setRunsByProject((current) => ({
        ...current,
        [projectId]: projectRuns,
      }));
      setSelectedRunId((current) => {
        if (preferredRunId && projectRuns.some((run) => run.id === preferredRunId)) {
          return preferredRunId;
        }
        if (current && projectRuns.some((run) => run.id === current)) {
          return current;
        }
        return projectRuns[0]?.id ?? null;
      });
    },
    []
  );

  useEffect(() => {
    void loadWorkspaceData();
  }, [loadWorkspaceData]);

  useEffect(() => {
    if (!selectedProjectId) {
      return;
    }

    let isMounted = true;
    const refresh = async () => {
      try {
        const projectRuns = await runsApi.listForProject(selectedProjectId);
        if (!isMounted) {
          return;
        }
        setRunsByProject((current) => ({
          ...current,
          [selectedProjectId]: projectRuns,
        }));
        setSelectedRunId((current) => {
          if (current && projectRuns.some((run) => run.id === current)) {
            return current;
          }
          return projectRuns[0]?.id ?? null;
        });
      } catch {
        // Keep previous data and retry on next interval.
      }
    };

    const interval = window.setInterval(() => {
      void refresh();
    }, REFRESH_INTERVAL_MS);

    return () => {
      isMounted = false;
      window.clearInterval(interval);
    };
  }, [selectedProjectId]);

  useEffect(() => {
    if (!selectedRunId) {
      setArtifacts([]);
      return;
    }

    let isMounted = true;

    const refreshArtifacts = async () => {
      try {
        const runArtifacts = await artifactsApi.listByRunId(selectedRunId);
        if (isMounted) {
          setArtifacts(runArtifacts);
        }
      } catch {
        if (isMounted) {
          setArtifacts([]);
        }
      }
    };

    void refreshArtifacts();
    const interval = window.setInterval(() => {
      void refreshArtifacts();
    }, REFRESH_INTERVAL_MS);

    return () => {
      isMounted = false;
      window.clearInterval(interval);
    };
  }, [selectedRunId]);

  const handleCreateProject = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!newProjectIdea.trim()) {
      setError("Project idea is required.");
      return;
    }

    setIsCreatingProject(true);
    setError("");

    try {
      const created = await projectsApi.create({
        idea: newProjectIdea.trim(),
        name: newProjectName.trim() ? newProjectName.trim() : undefined,
      });
      setIsCreateProjectOpen(false);
      setNewProjectName("");
      setNewProjectIdea("");
      await loadWorkspaceData(created.id);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
    } finally {
      setIsCreatingProject(false);
    }
  };

  const handleStartRun = async () => {
    if (!selectedProject) {
      return;
    }

    setIsStartingRun(true);
    setError("");

    try {
      const run = await runsApi.startForProject(selectedProject.id);
      await refreshRunsForProject(selectedProject.id, run.id);
      setSelectedRunId(run.id);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
    } finally {
      setIsStartingRun(false);
    }
  };

  const dashboardProjects = useMemo(
    () => projects.map((project) => toDashboardProject(project, runsByProject[project.id] ?? [], integrations, null, [])),
    [projects, runsByProject, integrations]
  );

  const dashboardProject = useMemo(() => {
    if (!selectedProject) {
      return null;
    }

    return toDashboardProject(
      selectedProject,
      selectedProjectRuns,
      integrations,
      selectedRunId,
      artifacts
    );
  }, [artifacts, integrations, selectedProject, selectedProjectRuns, selectedRunId]);

  const runItems: RunItem[] = useMemo(
    () => selectedProjectRuns.map(toRunItem),
    [selectedProjectRuns]
  );

  const artifactItems: ArtifactItem[] = useMemo(
    () => artifacts.map(toArtifactItem),
    [artifacts]
  );

  if (isLoading) {
    return <p className="p-8 text-slate-600">Loading workspace...</p>;
  }

  if (!dashboardProject) {
    return (
      <AppShell
        sidebar={
          <Sidebar
            user={CURRENT_USER}
            projects={dashboardProjects}
            selectedProjectId=""
            onSelectProject={setSelectedProjectId}
            onCreateProject={() => setIsCreateProjectOpen(true)}
            onOpenSettings={() => navigate("/settings/integrations")}
          />
        }
      >
        <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-card">
          <h2 className="text-xl font-semibold text-slate-900">No Projects Found</h2>
          <p className="mt-2 text-sm text-slate-600">
            Create a project to start the workflow orchestration.
          </p>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell
      sidebar={
        <Sidebar
          user={CURRENT_USER}
          projects={dashboardProjects}
          selectedProjectId={dashboardProject.id}
          onSelectProject={setSelectedProjectId}
          onCreateProject={() => setIsCreateProjectOpen(true)}
          onOpenSettings={() => navigate("/settings/integrations")}
        />
      }
    >
      <div className="space-y-6 pb-6">
        {isCreateProjectOpen && (
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
            <h3 className="text-sm font-semibold text-slate-900">Create Project</h3>
            <form className="mt-4 space-y-3" onSubmit={handleCreateProject}>
              <input
                value={newProjectName}
                onChange={(event) => setNewProjectName(event.target.value)}
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-slate-500"
                placeholder="Name (optional)"
              />
              <textarea
                value={newProjectIdea}
                onChange={(event) => setNewProjectIdea(event.target.value)}
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-slate-500"
                placeholder="Project idea"
                rows={4}
                required
              />
              <div className="flex items-center gap-2">
                <button
                  type="submit"
                  disabled={isCreatingProject}
                  className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                >
                  {isCreatingProject ? "Creating..." : "Create"}
                </button>
                <button
                  type="button"
                  onClick={() => setIsCreateProjectOpen(false)}
                  className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-400"
                >
                  Cancel
                </button>
              </div>
            </form>
          </section>
        )}

        <TopHeader
          project={dashboardProject}
          onNewRun={handleStartRun}
          isStartingRun={isStartingRun}
          canViewLatestRun={Boolean(selectedRunId)}
          onViewLatestRun={() => {
            if (selectedRunId) {
              navigate(`/runs/${selectedRunId}`);
            }
          }}
        />

        {error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        )}

        <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Runs" value={String(dashboardProject.stats.runs)} />
          <StatCard label="Success Rate" value={dashboardProject.stats.successRate} />
          <StatCard label="Artifacts" value={String(dashboardProject.stats.artifacts)} />
          <StatCard label="Completed Runs" value={String(dashboardProject.stats.completedRuns)} />
        </section>

        <section className="grid grid-cols-1 gap-4 xl:grid-cols-12">
          <div className="xl:col-span-7">
            <RunList
              runs={runItems}
              selectedRunId={selectedRunId}
              onSelectRun={setSelectedRunId}
              onOpenRun={(runId) => navigate(`/runs/${runId}`)}
            />
          </div>
          <div className="xl:col-span-5">
            <ProjectDetails project={dashboardProject} />
          </div>
        </section>

        <section className="grid grid-cols-1 gap-4 xl:grid-cols-12">
          <div className="xl:col-span-8">
            <ArtifactList artifacts={artifactItems} />
          </div>
          <div className="xl:col-span-4">
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
              <h3 className="mb-4 text-sm font-semibold text-slate-900">Integrations Summary</h3>
              <div className="space-y-3">
                {integrations.map((integration) => (
                  <IntegrationSettingsCard key={integration.id} integration={integration} />
                ))}
              </div>
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  );
}

type StatCardProps = {
  label: string;
  value: string;
};

function StatCard({ label, value }: StatCardProps) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-card">
      <p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-bold tracking-tight text-slate-950">{value}</p>
    </article>
  );
}

function toRunItem(run: WorkflowRun): RunItem {
  return {
    id: run.id,
    name: `Run ${run.id.slice(0, 8)}`,
    status: run.status,
    currentStep: run.current_step,
    createdAt: formatDate(run.created_at),
    updatedAt: formatDate(run.updated_at),
    artifactsCount: run.artifacts.length,
  };
}

function toArtifactItem(artifact: Artifact): ArtifactItem {
  return {
    id: artifact.id,
    title: artifact.title,
    type: artifact.artifact_type,
    createdAt: formatDate(artifact.created_at),
  };
}

function toDashboardProject(
  project: ApiProject,
  runs: WorkflowRun[],
  integrations: Integration[],
  selectedRunId: string | null,
  artifacts: Artifact[]
): Project {
  const terminalRuns = runs.filter((run) => run.status === "completed" || run.status === "failed");
  const successfulRuns = terminalRuns.filter((run) => run.status === "completed");
  const successRate = terminalRuns.length
    ? `${Math.round((successfulRuns.length / terminalRuns.length) * 100)}%`
    : "N/A";
  const completedRuns = successfulRuns.length;
  const artifactCount = runs.reduce((sum, run) => sum + run.artifacts.length, 0);

  return {
    id: project.id,
    name: project.name,
    description: project.idea,
    status: project.status,
    createdAt: formatDate(project.created_at),
    stats: {
      runs: runs.length,
      successRate,
      artifacts: artifactCount,
      completedRuns,
    },
    children: [
      { id: `${project.id}-runs`, label: "runs", type: "runs", count: runs.length },
      { id: `${project.id}-artifacts`, label: "artifacts", type: "artifacts", count: artifactCount },
      {
        id: `${project.id}-repo`,
        label: "repo",
        type: "repo",
        count: selectedRunId ? artifacts.filter((item) => item.artifact_type === "generated_file").length : 0,
      },
      {
        id: `${project.id}-deployment`,
        label: "deployment",
        type: "deployment",
        count: completedRuns,
      },
    ],
    runs: runs.map(toRunItem),
    artifacts: artifacts.map(toArtifactItem),
    integrations,
    selectedRunId,
  };
}

function buildIntegrationsSummary(
  googleDriveConfig: GoogleDriveConnectionConfig | null,
  githubConfig: GitHubConnectionConfig | null,
  jiraConfig: JiraConnectionConfig | null
): Integration[] {
  const googleDriveStatus = googleDriveConfig?.enabled
    ? "connected"
    : hasGoogleDriveDraft(googleDriveConfig)
      ? "pending"
      : "not_connected";
  const githubStatus = githubConfig?.enabled
    ? "connected"
    : hasGitHubDraft(githubConfig)
      ? "pending"
      : "not_connected";
  const jiraStatus = jiraConfig?.enabled
    ? "connected"
    : hasJiraDraft(jiraConfig)
      ? "pending"
      : "not_connected";

  return [
    {
      id: "integration-google-drive",
      name: "Google Drive",
      status: googleDriveStatus,
      description: googleDriveStatus === "connected"
        ? `Connected: ${googleDriveConfig?.server_url ?? "configured"}`
        : googleDriveStatus === "pending"
          ? "Configured but disabled"
          : "Not configured",
    },
    {
      id: "integration-jira",
      name: "Jira",
      status: jiraStatus,
      description: jiraStatus === "connected"
        ? `Connected: ${jiraConfig?.server_url ?? "configured"}`
        : jiraStatus === "pending"
          ? "Configured but disabled"
          : "Not configured",
    },
    {
      id: "integration-github",
      name: "GitHub",
      status: githubStatus,
      description: githubStatus === "connected"
        ? `Connected: ${githubConfig?.server_url ?? "configured"}`
        : githubStatus === "pending"
          ? "Configured but disabled"
          : "Not configured",
    },
  ];
}

function hasGoogleDriveDraft(config: GoogleDriveConnectionConfig | null): boolean {
  if (!config) {
    return false;
  }

  return Boolean(
    config.server_url.trim() ||
      config.folder_id.trim() ||
      config.arguments_template_json.trim() ||
      config.read_arguments_template_json.trim()
  );
}

function hasGitHubDraft(config: GitHubConnectionConfig | null): boolean {
  if (!config) {
    return false;
  }

  return Boolean(
    config.server_url.trim() ||
      config.arguments_template_json.trim() ||
      config.owner.trim() ||
      config.repository.trim()
  );
}

function hasJiraDraft(config: JiraConnectionConfig | null): boolean {
  if (!config) {
    return false;
  }

  return Boolean(
    config.server_url.trim() ||
      config.arguments_template_json.trim() ||
      config.project_key.trim()
  );
}

function selectProjectId({
  projects,
  previousProjectId,
  preferredProjectId,
}: {
  projects: ApiProject[];
  previousProjectId: string;
  preferredProjectId?: string;
}): string {
  if (preferredProjectId && projects.some((project) => project.id === preferredProjectId)) {
    return preferredProjectId;
  }
  if (projects.some((project) => project.id === previousProjectId)) {
    return previousProjectId;
  }
  return projects[0]?.id ?? "";
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}
