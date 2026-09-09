import httpx
from fastapi import APIRouter, HTTPException

from app.services.server_sync import ServerSyncService

router = APIRouter()
service = ServerSyncService()


@router.get("/status")
async def status():
    return {
        "configured": service.configured,
        "base_url": service.base_url(),
        "device_id": service.device_id(),
    }


@router.post("/sync")
async def sync():
    if not service.configured:
        raise HTTPException(status_code=400, detail="Server sync is not configured (server URL or device token missing).")
    try:
        return service.sync()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Server request failed: {exc}") from exc
