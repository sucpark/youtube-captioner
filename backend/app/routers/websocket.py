"""WebSocket router for real-time progress updates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections per job."""

    def __init__(self):
        self.active_connections: dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()
        self.active_connections[job_id].add(websocket)
        logger.info(f"WebSocket connected: job_id={job_id}")

    def disconnect(self, websocket: WebSocket, job_id: str):
        """Remove a WebSocket connection."""
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
        logger.info(f"WebSocket disconnected: job_id={job_id}")

    async def broadcast(self, job_id: str, data: dict):
        """Broadcast message to all connections for a job."""
        if job_id not in self.active_connections:
            return

        disconnected = set()
        for connection in self.active_connections[job_id]:
            try:
                await connection.send_json(data)
            except Exception:
                disconnected.add(connection)

        for connection in disconnected:
            self.active_connections[job_id].discard(connection)


manager = ConnectionManager()


@router.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for job progress updates."""
    await manager.connect(websocket, job_id)
    try:
        while True:
            # Keep connection alive, wait for client messages
            data = await websocket.receive_text()
            # Echo back for ping/pong
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, job_id)


async def send_progress(job_id: str, status: str, progress: int, message: str = ""):
    """Send progress update to all connected clients."""
    await manager.broadcast(job_id, {
        "type": "progress",
        "status": status,
        "progress": progress,
        "message": message,
    })


async def send_completed(job_id: str, result: dict):
    """Send completion message to all connected clients."""
    await manager.broadcast(job_id, {
        "type": "completed",
        "status": "completed",
        "progress": 100,
        "result": result,
    })


async def send_error(job_id: str, error: str):
    """Send error message to all connected clients."""
    await manager.broadcast(job_id, {
        "type": "error",
        "status": "failed",
        "error": error,
    })
