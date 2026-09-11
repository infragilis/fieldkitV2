"""In-place appliance updates: check the server for a new bundle and apply it."""

import json
import os
import subprocess
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.services.server_sync import DEVICE_TOKEN_ENV
from app.services.settings_store import SettingsStore

router = APIRouter()
UPDATE_SCRIPT = Path("/opt/fieldkit/scripts/update_appliance.sh")
VERSION_PATH = Path("/opt/fieldkit/pyproject.toml")
FALLBACK_VERSION = "0.1.6"


def local_version() -> str:
    try:
        for line in VERSION_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("version"):
                return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return FALLBACK_VERSION


def _client():
    settings = get_settings()
    config = SettingsStore().load().server_sync
    token = os.environ.get(DEVICE_TOKEN_ENV) or config.device_token
    return httpx.Client(
        base_url=(config.base_url or settings.server_base_url).rstrip("/") + "/",
        headers={"Authorization": f"Bearer {token}"},
        timeout=httpx.Timeout(30.0, connect=10.0),
    ), config


def _compare(current: str, latest: str) -> int:
    def parts(value):
        return [int(part) for part in value.split(".")[:3]]

    try:
        a, b = parts(current), parts(latest)
    except ValueError:
        return -1
    for left, right in zip(a, b):
        if left != right:
            return 1 if left > right else -1
    return 0


@router.get("/update/latest")
def update_latest() -> dict:
    current = local_version()
    try:
        with _client()[0] as client:
            response = client.get("api/v1/device/update-latest")
            response.raise_for_status()
            payload = response.json()
    except Exception:
        return {"available": False, "local_version": current, "error": "Could not reach the update server."}
    if not payload.get("available"):
        return {"available": False, "local_version": current}
    return {
        "available": True,
        "local_version": current,
        "latest_version": payload["version"],
        "update_available": _compare(current, payload["version"]) < 0,
        "url": payload["url"],
        "sha256": payload["sha256"],
        "published_at": payload.get("published_at"),
    }


@router.post("/update/apply", status_code=202)
def update_apply(payload: dict) -> dict:
    version = str(payload.get("version") or "")
    url = str(payload.get("url") or "")
    sha256 = str(payload.get("sha256") or "")
    if not version or not url or not sha256 or len(sha256) != 64:
        raise HTTPException(status_code=400, detail="version, url and sha256 are required")
    if not UPDATE_SCRIPT.is_file():
        raise HTTPException(status_code=501, detail="Update script not installed")
    try:
        subprocess.Popen(
            ["sudo", "/bin/bash", str(UPDATE_SCRIPT), version, url, sha256],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not start the update: {exc}") from exc
    return {"started": True, "version": version}
