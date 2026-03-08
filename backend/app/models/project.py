from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

ProjectStatus = Literal["draft", "in_progress", "completed"]


class ProjectCreate(BaseModel):
    idea: str = Field(..., min_length=1, max_length=5000)
    name: str | None = Field(default=None, min_length=1, max_length=120)

    @field_validator("idea", mode="before")
    @classmethod
    def normalize_idea(cls, value: object) -> object:
        if isinstance(value, str):
            return " ".join(value.split())
        return value

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = " ".join(value.split())
            return normalized or None
        return value


class Project(BaseModel):
    id: str
    name: str
    idea: str
    status: ProjectStatus
    created_at: datetime
