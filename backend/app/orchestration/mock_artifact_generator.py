from dataclasses import dataclass
from textwrap import dedent

from app.models.artifact import ArtifactType
from app.models.project import Project
from app.models.workflow_run import WorkflowStepName


@dataclass(frozen=True)
class ArtifactDraft:
    artifact_type: ArtifactType
    title: str
    content: str


class MockArtifactGenerator:
    """Produces realistic placeholder artifact content for mocked workflows."""

    def generate(
        self,
        completed_step: WorkflowStepName,
        project: Project,
    ) -> ArtifactDraft | None:
        if completed_step == "high_level_design":
            return ArtifactDraft(
                artifact_type="high_level_design",
                title="High-Level Design",
                content=self._high_level_design(project),
            )

        if completed_step == "detailed_design":
            return ArtifactDraft(
                artifact_type="detailed_design",
                title="Detailed Technical Design",
                content=self._detailed_design(project),
            )

        if completed_step == "code_generation":
            return ArtifactDraft(
                artifact_type="code_summary",
                title="Code Generation Summary",
                content=self._code_summary(project),
            )

        if completed_step == "test_execution":
            return ArtifactDraft(
                artifact_type="test_summary",
                title="Test Execution Summary",
                content=self._test_summary(project),
            )

        return None

    def _high_level_design(self, project: Project) -> str:
        return dedent(
            f"""
            # High-Level Design

            Product: {project.name}

            ## Objective
            Deliver an end-to-end experience for the idea: "{project.idea}".

            ## Core Components
            - Frontend SPA for user interactions and orchestration visibility.
            - Backend API for project, workflow, and artifact lifecycle.
            - MongoDB persistence for projects, runs, and generated outputs.

            ## Main Flow
            1. User creates a project.
            2. User starts generation run.
            3. Workflow advances through design/code/test stages.
            4. Generated artifacts are attached to the run and rendered in UI.
            """
        ).strip()

    def _detailed_design(self, project: Project) -> str:
        return dedent(
            f"""
            # Detailed Technical Design

            Project: {project.name}

            ## API Boundaries
            - `/api/projects` for project creation and retrieval.
            - `/api/projects/{{project_id}}/runs` for run orchestration start/listing.
            - `/api/runs/{{run_id}}/artifacts` for run-scoped output retrieval.

            ## Data Contracts
            - Project document stores core business intent and metadata.
            - WorkflowRun document tracks progression, current step, and artifact IDs.
            - Artifact document stores output payloads for design/code/test stages.

            ## Execution Strategy
            - Background orchestrator advances one step at a fixed delay.
            - Step completion triggers deterministic mocked artifact generation.
            - Run details page polls every 2.5 seconds for status and artifacts.
            """
        ).strip()

    def _code_summary(self, project: Project) -> str:
        return dedent(
            f"""
            # Code Summary

            Project: {project.name}

            ## Implemented Modules
            - Domain models for project/run/artifact entities.
            - Repository layer with MongoDB persistence.
            - Mock orchestration engine with timed step transitions.
            - Frontend run dashboard with timeline and artifact browser.

            ## Notable Decisions
            - Async repository contracts to keep storage adapter-agnostic.
            - Artifact model designed for future AI-generated content replacement.
            - Minimal API surface with typed schemas for stable frontend integration.
            """
        ).strip()

    def _test_summary(self, project: Project) -> str:
        return dedent(
            f"""
            # Test Summary

            Project: {project.name}

            ## Smoke Checks
            - API startup and MongoDB connectivity: passed.
            - Workflow progression from intake to completed: passed.
            - Artifact generation and retrieval endpoints: passed.
            - Frontend build with run polling and artifact rendering: passed.

            ## Observations
            - Polling interval provides near-real-time UI updates without heavy load.
            - Artifact retrieval remains stable while run is still progressing.
            """
        ).strip()
