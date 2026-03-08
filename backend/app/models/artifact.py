from datetime import datetime
from typing import Literal

from pydantic import BaseModel

ArtifactType = Literal[
    "high_level_design",
    "detailed_design",
    "code_summary",
    "test_summary",
]


class Artifact(BaseModel):
    id: str
    run_id: str
    project_id: str
    artifact_type: ArtifactType
    title: str
    content: str
    created_at: datetime
