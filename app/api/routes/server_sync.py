import httpx
from fastapi import APIRouter, HTTPException

from app.core.models import ServerSyncConfig
from app.services.server_sync import ServerSyncService
from app.services.settings_store import SettingsStore

router = APIRouter()
service = ServerSyncService()
store = SettingsStore()


@router.get("/status")
async def status():
    return {
        "configured": service.configured,
        "base_url": service.base_url(),
        "device_id": service.device_id(),
    }


@router.put("/config")
async def set_config(payload: ServerSyncConfig):
    settings = store.load()
    settings.server_sync = payload
    store.save(settings)
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
