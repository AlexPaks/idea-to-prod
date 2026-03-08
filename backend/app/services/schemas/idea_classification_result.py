from typing import Literal

from pydantic import BaseModel, Field


Complexity = Literal["low", "medium", "high"]


class IdeaClassificationResult(BaseModel):
    project_type: str
    domain: str
    target_users: list[str] = Field(default_factory=list)
    primary_interfaces: list[str] = Field(default_factory=list)
    core_features: list[str] = Field(default_factory=list)
    secondary_features: list[str] = Field(default_factory=list)
    data_complexity: Complexity
    business_logic_complexity: Complexity
    integration_complexity: Complexity
    recommended_template: str
    recommended_architecture_pattern: str
    notes: list[str] = Field(default_factory=list)
