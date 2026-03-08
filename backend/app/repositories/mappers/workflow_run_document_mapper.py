from typing import Any

from app.models.workflow_run import WorkflowRun


def workflow_run_to_document(run: WorkflowRun) -> dict[str, Any]:
    document = run.model_dump(mode="python")
    document["_id"] = document.pop("id")
    return document


def document_to_workflow_run(document: dict[str, Any]) -> WorkflowRun:
    payload = dict(document)
    payload["id"] = str(payload.pop("_id"))
    return WorkflowRun.model_validate(payload)
