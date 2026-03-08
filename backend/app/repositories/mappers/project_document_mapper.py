from typing import Any

from app.models.project import Project


def project_to_document(project: Project) -> dict[str, Any]:
    return {
        "_id": project.id,
        "name": project.name,
        "idea": project.idea,
        "status": project.status,
        "created_at": project.created_at,
    }


def document_to_project(document: dict[str, Any]) -> Project:
    return Project(
        id=str(document["_id"]),
        name=str(document["name"]),
        idea=str(document["idea"]),
        status=str(document["status"]),
        created_at=document["created_at"],
    )
