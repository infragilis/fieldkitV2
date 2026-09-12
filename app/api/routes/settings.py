from fastapi import APIRouter

from app.core.models import AppSettingsPayload
from app.services.settings_store import SettingsStore

router = APIRouter()
store = SettingsStore()


def _redacted(payload: AppSettingsPayload) -> dict:
    """Never send stored secrets back to clients; report only their presence."""
    data = payload.model_dump()
    data["wifi"]["password"] = ""
    data["server_sync"]["device_token"] = ""
    data["server_sync"]["device_token_configured"] = bool(payload.server_sync.device_token)
    return data


@router.get("")
async def get_settings():
    return _redacted(store.load())


@router.put("")
async def update_settings(payload: AppSettingsPayload):
    existing = store.load()
    if "server_sync" not in payload.model_fields_set:
        payload.server_sync = existing.server_sync
    else:
        # Blank secrets mean "keep the stored value" (the client never receives them).
        if not payload.server_sync.device_token:
            payload.server_sync.device_token = existing.server_sync.device_token
        if not payload.server_sync.base_url:
            payload.server_sync.base_url = existing.server_sync.base_url
    if not payload.wifi.password:
        payload.wifi.password = existing.wifi.password
    return _redacted(store.save(payload))
