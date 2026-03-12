from pydantic import BaseModel, Field


class ArchitectureResult(BaseModel):
    frontend_stack: str
    backend_stack: str
    database: str
    auth_strategy: str
    deployment_shape: str
    background_jobs: list[str] = Field(default_factory=list)
    recommended_modules: list[str] = Field(default_factory=list)
    recommended_entities: list[str] = Field(default_factory=list)
    api_groups: list[str] = Field(default_factory=list)
    frontend_pages: list[str] = Field(default_factory=list)
    testing_strategy: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
