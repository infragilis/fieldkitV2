from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.services.serial import SerialService

router = APIRouter()
serial_service = SerialService()


@router.get("/ports")
async def serial_ports():
    return {"ports": serial_service.list_ports()}


@router.get("/adapters")
async def serial_adapters():
    return {"adapters": serial_service.list_adapters()}


@router.get("/sessions")
async def serial_sessions():
    return {"sessions": serial_service.session_status()}


@router.post("/reset/{profile_index}")
async def reset_serial_console(profile_index: int):
    try:
        reset = await serial_service.reset_console(profile_index)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"reset": reset, "index": profile_index}


@router.websocket("/ws/{profile_index}")
async def serial_console(websocket: WebSocket, profile_index: int):
    await websocket.accept()
    try:
        await serial_service.stream_console(profile_index, websocket)
    except WebSocketDisconnect:
        return
