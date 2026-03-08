from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

ArtifactType = Literal[
    "high_level_design",
    "detailed_design",
    "code_summary",
    "test_summary",
    "generated_file",
]


class Artifact(BaseModel):
    id: str
    run_id: str
    project_id: str
    artifact_type: ArtifactType
    title: str
    content: str
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)
