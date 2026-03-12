from typing import Literal

from pydantic import BaseModel, Field


RepairAction = Literal["create", "update", "delete"]


class RepairChange(BaseModel):
    path: str
    action: RepairAction
    reason: str
    content: str = ""


class RepairResult(BaseModel):
    repair_summary: str
    failure_type: str
    root_cause: str
    changes: list[RepairChange] = Field(default_factory=list)
