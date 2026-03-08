from typing import Any

from app.models.artifact import Artifact


def artifact_to_document(artifact: Artifact) -> dict[str, Any]:
    payload = artifact.model_dump(mode="python")
    payload["_id"] = payload.pop("id")
    return payload


def document_to_artifact(document: dict[str, Any]) -> Artifact:
    payload = dict(document)
    payload["id"] = str(payload.pop("_id"))
    return Artifact.model_validate(payload)
