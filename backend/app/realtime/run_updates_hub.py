import asyncio
import logging
from collections import defaultdict

from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder

from app.models.workflow_run import WorkflowRun

logger = logging.getLogger(__name__)


class RunUpdatesHub:
    """Tracks run-specific websocket subscribers and broadcasts run updates."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, run_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[run_id].add(websocket)
        logger.info("WebSocket client subscribed to run '%s'", run_id)

    async def disconnect(self, run_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            subscribers = self._connections.get(run_id)
            if not subscribers:
                return
            subscribers.discard(websocket)
            if not subscribers:
                self._connections.pop(run_id, None)
        logger.info("WebSocket client unsubscribed from run '%s'", run_id)

    async def send_snapshot(self, websocket: WebSocket, run: WorkflowRun) -> None:
        payload = {
            "type": "run.updated",
            "run": jsonable_encoder(run),
        }
        await websocket.send_json(payload)

    async def publish_run_update(self, run: WorkflowRun) -> None:
        payload = {
            "type": "run.updated",
            "run": jsonable_encoder(run),
        }
        await self._broadcast(run.id, payload)

    async def _broadcast(self, run_id: str, payload: dict[str, object]) -> None:
        async with self._lock:
            subscribers = list(self._connections.get(run_id, set()))

        if not subscribers:
            return

        stale_subscribers: list[WebSocket] = []
        for websocket in subscribers:
            try:
                await websocket.send_json(payload)
            except Exception:
                stale_subscribers.append(websocket)

        if stale_subscribers:
            async with self._lock:
                active_subscribers = self._connections.get(run_id)
                if not active_subscribers:
                    return
                for websocket in stale_subscribers:
                    active_subscribers.discard(websocket)
                if not active_subscribers:
                    self._connections.pop(run_id, None)
