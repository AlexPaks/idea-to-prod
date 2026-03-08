from pydantic import BaseModel, Field


class CodeGenerationFileEntry(BaseModel):
    path: str
    content: str


class CodeGenerationResult(BaseModel):
    files: list[CodeGenerationFileEntry] = Field(default_factory=list)
