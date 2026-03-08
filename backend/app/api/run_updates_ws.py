import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.realtime.run_updates_hub import RunUpdatesHub
from app.services.workflow_run_service import WorkflowRunService

router = APIRouter(tags=["run-updates"])
logger = logging.getLogger(__name__)


def _get_run_updates_hub(websocket: WebSocket) -> RunUpdatesHub:
    return websocket.app.state.run_updates_hub


def _get_workflow_run_service(websocket: WebSocket) -> WorkflowRunService:
    return websocket.app.state.workflow_run_service


@router.websocket("/ws/runs/{run_id}")
async def subscribe_run_updates(websocket: WebSocket, run_id: str) -> None:
    run_service = _get_workflow_run_service(websocket)
    run_updates_hub = _get_run_updates_hub(websocket)

    run = await run_service.get_run(run_id)
    if run is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Run not found")
        return

    await run_updates_hub.connect(run_id, websocket)
    try:
        await run_updates_hub.send_snapshot(websocket, run)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for run '%s'", run_id)
    finally:
        await run_updates_hub.disconnect(run_id, websocket)
