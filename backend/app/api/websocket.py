import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
from app.api.simulation import simulation_engine

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_state(self, state_data: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(state_data)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/ws/simulation")
async def websocket_simulation_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            if simulation_engine:
                state = simulation_engine.get_state().dict()
                await websocket.send_json(state)
            await asyncio.sleep(0.5)  # Stream every 500ms
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
