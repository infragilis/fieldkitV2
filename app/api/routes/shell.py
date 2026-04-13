from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.local_shell import LocalShellService

router = APIRouter()
shell_service = LocalShellService()


@router.websocket("/ws")
async def local_shell(websocket: WebSocket):
    await websocket.accept()
    try:
        await shell_service.stream_shell(websocket)
    except WebSocketDisconnect:
        return
