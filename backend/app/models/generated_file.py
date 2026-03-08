from datetime import datetime

from pydantic import BaseModel


class GeneratedFileMetadata(BaseModel):
    path: str
    artifact_id: str
    size_bytes: int
    language: str | None = None
    updated_at: datetime


class GeneratedFileContent(BaseModel):
    path: str
    content: str
    language: str | None = None
