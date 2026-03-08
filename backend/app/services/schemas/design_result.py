from pydantic import BaseModel


class DesignResult(BaseModel):
    title: str
    summary: str
    content: str
