from typing import Literal

from fastapi import APIRouter, HTTPException

from app.core.models import ServerSyncConfig
from app.services.server_sync import ServerSyncService
from app.services.server_sync_job import ServerSyncJob
from app.services.settings_store import SettingsStore

router = APIRouter()
service = ServerSyncService()
job = ServerSyncJob(service)
store = SettingsStore()


@router.get("/status")
async def status():
    return {
        "configured": service.configured,
        "base_url": service.base_url(),
        "device_id": service.device_id(),
        "schedule": {"startup_delay_seconds": 600, "interval_seconds": 3600},
        **job.status(),
    }


@router.put("/config")
async def set_config(payload: ServerSyncConfig):
    if job.status()["running"]:
        raise HTTPException(status_code=409, detail="Wait for the current sync to finish before changing its configuration.")
    settings = store.load()
    if not payload.device_token:
        payload.device_token = settings.server_sync.device_token
    settings.server_sync = payload
    store.save(settings)
    return {
        "configured": service.configured,
        "base_url": service.base_url(),
        "device_id": service.device_id(),
    }


@router.post("/sync", status_code=202)
async def sync(trigger: Literal["manual", "scheduled"] = "manual"):
    if not service.configured:
        if trigger == "scheduled":
            return {"started": False, "reason": "not_configured", **job.status()}
        raise HTTPException(status_code=400, detail="Server sync is not configured (server URL or device token missing).")
    started = job.start(trigger)
    return {"started": started, **job.status()}
