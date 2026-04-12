from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.serial import SerialService

router = APIRouter()
serial_service = SerialService()


@router.get("/ports")
async def serial_ports():
    return {"ports": serial_service.list_ports()}


@router.get("/sessions")
async def serial_sessions():
    return {"sessions": serial_service.session_status()}


@router.websocket("/ws/{profile_index}")
async def serial_console(websocket: WebSocket, profile_index: int):
    await websocket.accept()
    try:
        await serial_service.stream_console(profile_index, websocket)
    except WebSocketDisconnect:
        return
