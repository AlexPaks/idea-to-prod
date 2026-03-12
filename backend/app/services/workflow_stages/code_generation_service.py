import logging
import re
from textwrap import dedent

from app.models.artifact import Artifact
from app.repositories.artifact_repository import ArtifactRepository
from app.services.workflow_stage_models import (
    StageArtifactDraft,
    StageExecutionContext,
    StageExecutionResult,
    StageGeneratedFileDraft,
)

logger = logging.getLogger(__name__)


class CodeGenerationService:
    step_name = "code_generation"

    def __init__(self, artifact_repository: ArtifactRepository) -> None:
        self._artifact_repository = artifact_repository

    async def execute(self, context: StageExecutionContext) -> StageExecutionResult:
        logger.info(
            "Running stage '%s' for run '%s' and project '%s'",
            self.step_name,
            context.run.id,
            context.project.id,
        )

        detailed_design = await self._load_latest_detailed_design(context.run.id)
        detailed_design_content = (
            detailed_design.content.strip()
            if detailed_design is not None
            else _build_fallback_detailed_design(context.project.name, context.project.idea)
        )
        extracted_endpoints = _extract_api_endpoints(detailed_design_content)
        design_highlights = _extract_bullet_highlights(detailed_design_content)

        logs = [
            (
                f"Loaded detailed design artifact '{detailed_design.id}' as code-generation input."
                if detailed_design is not None
                else "Detailed design artifact unavailable; used synthesized fallback design context."
            ),
            f"Derived {len(extracted_endpoints)} API route(s) from detailed design content.",
            "Generated implementation placeholders anchored to detailed design highlights.",
        ]

        artifact = StageArtifactDraft(
            artifact_type="code_summary",
            title="Code Generation Summary",
            content=dedent(
                f"""
                # Code Summary

                Project: {context.project.name}

                ## Detailed Design Input
                - Source: {"artifact:detailed_design" if detailed_design is not None else "fallback_synthesized"}
                - Captured API routes: {len(extracted_endpoints)}

                ## Design Highlights Applied
                {_format_markdown_bullets(design_highlights)}

                ## Implemented Modules
                - API stubs inferred from detailed design route definitions.
                - Frontend scaffold that displays design-driven implementation notes.
                - Backend entrypoint with route handlers mapped from design input.

                ## Notable Decisions
                - Code generation now consumes latest detailed design artifact per run.
                - Route handlers are generated deterministically from extracted design paths.
                - Fallback design context preserves flow even when upstream artifact is missing.
                """
            ).strip(),
            metadata={
                "mock_source": "code_generation_service",
                "design_input_artifact_id": detailed_design.id if detailed_design is not None else None,
                "derived_route_count": len(extracted_endpoints),
            },
        )

        return StageExecutionResult(
            step=self.step_name,
            summary="Generated code summary and files from detailed design input",
            logs=logs,
            artifacts=[artifact],
            generated_files=[
                StageGeneratedFileDraft(
                    relative_path="frontend/src/App.tsx",
                    language="typescript",
                    description="Generated frontend entry page from detailed design highlights",
                    content=_render_frontend_app(
                        project_name=context.project.name,
                        project_idea=context.project.idea,
                        design_highlights=design_highlights,
                    ),
                ),
                StageGeneratedFileDraft(
                    relative_path="backend/main.py",
                    language="python",
                    description="Generated backend startup placeholder from detailed design routes",
                    content=_render_backend_main(
                        project_name=context.project.name,
                        endpoint_paths=extracted_endpoints,
                    ),
                ),
            ],
            metadata={"artifact_count": 1, "generated_file_count": 2},
        )

    async def _load_latest_detailed_design(self, run_id: str) -> Artifact | None:
        try:
            artifacts = await self._artifact_repository.list_by_run_id(run_id)
        except Exception:
            logger.exception(
                "Failed to list artifacts while preparing code generation input for run '%s'",
                run_id,
            )
            return None

        detailed_design_artifacts = [
            artifact for artifact in artifacts if artifact.artifact_type == "detailed_design"
        ]
        if not detailed_design_artifacts:
            return None
        return detailed_design_artifacts[-1]


def _build_fallback_detailed_design(project_name: str, project_idea: str) -> str:
    return dedent(
        f"""
        # Detailed Technical Design

        Project: {project_name}

        ## API Boundaries
        - `/api/projects` for project creation and retrieval.
        - `/api/projects/{{project_id}}/runs` for run orchestration.
        - `/api/runs/{{run_id}}/artifacts` for run output retrieval.

        ## UX
        - Display project purpose: {project_idea}
        """
    ).strip()


def _extract_api_endpoints(design_content: str) -> list[str]:
    matches = re.findall(r"`(/[^`]+)`", design_content)
    unique_paths: list[str] = []
    for path in matches:
        if path not in unique_paths:
            unique_paths.append(path)
    return unique_paths


def _extract_bullet_highlights(design_content: str, limit: int = 6) -> list[str]:
    highlights: list[str] = []
    for line in design_content.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            highlights.append(stripped[2:].strip())
        if len(highlights) >= limit:
            break

    if highlights:
        return highlights
    return [
        "No explicit bullets found in detailed design artifact.",
        "Used fallback implementation scaffolding.",
    ]


def _format_markdown_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _render_frontend_app(
    project_name: str,
    project_idea: str,
    design_highlights: list[str],
) -> str:
    highlight_lines = "\n".join(
        f'        <li key="{index}">{_escape_tsx_text(highlight)}</li>'
        for index, highlight in enumerate(design_highlights, start=1)
    )
    return dedent(
        f"""
        export default function App() {{
          return (
            <main>
              <h1>{_escape_tsx_text(project_name)}</h1>
              <p>{_escape_tsx_text(project_idea)}</p>
              <section>
                <h2>Detailed Design Highlights</h2>
                <ul>
{highlight_lines}
                </ul>
              </section>
            </main>
          );
        }}
        """
    ).strip()


def _render_backend_main(project_name: str, endpoint_paths: list[str]) -> str:
    routes = endpoint_paths if endpoint_paths else ["/api/projects", "/api/runs/{run_id}/artifacts"]
    route_handlers = "\n\n".join(
        dedent(
            f"""
            @app.get("{path}")
            async def {_route_name(path)}() -> dict[str, str]:
                return {{
                    "route": "{path}",
                    "source": "detailed_design",
                }}
            """
        ).strip()
        for path in routes
    )

    return dedent(
        f"""
        from fastapi import FastAPI

        app = FastAPI(title="{project_name} API")

        @app.get("/health")
        async def health() -> dict[str, str]:
            return {{"status": "ok", "project": "{project_name}"}}

        {route_handlers}
        """
    ).strip()


def _route_name(path: str) -> str:
    normalized = path.strip("/").replace("{", "").replace("}", "")
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", normalized).strip("_")
    return f"route_{normalized or 'root'}"


def _escape_tsx_text(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("{", "&#123;")
        .replace("}", "&#125;")
    )
