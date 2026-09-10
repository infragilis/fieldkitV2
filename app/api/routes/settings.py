from fastapi import APIRouter

from app.core.models import AppSettingsPayload
from app.services.settings_store import SettingsStore

router = APIRouter()
store = SettingsStore()


@router.get("")
async def get_settings():
    return store.load().model_dump()


@router.put("")
async def update_settings(payload: AppSettingsPayload):
    if "server_sync" not in payload.model_fields_set:
        payload.server_sync = store.load().server_sync
    saved = store.save(payload)
    return saved.model_dump()
