"""In-place appliance updates: check the server for a new bundle and apply it."""

import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException

from app.core.config import get_settings  # retained for route-test/runtime compatibility
from app.services.server_sync import ServerSyncService
from app.services.settings_store import SettingsStore

router = APIRouter()
UPDATE_SCRIPT = Path("/opt/fieldkit/scripts/update_appliance.sh")
ROLLBACK_SCRIPT = Path("/opt/fieldkit/scripts/rollback_appliance.sh")
STATUS_PATH = Path("/opt/fieldkit/runtime/state/update-state.json")
VERSION_PATH = Path("/opt/fieldkit/pyproject.toml")
FALLBACK_VERSION = "0.1.6"
_VERSION_RE = re.compile(r"^\d+(\.\d+){1,2}$")
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def local_version() -> str:
    try:
        for line in VERSION_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("version"):
                return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return FALLBACK_VERSION


def _client():
    service = ServerSyncService()
    base_url, token = service.connection_config()
    config = SettingsStore().load().server_sync
    return httpx.Client(
        base_url=base_url + "/",
        headers={"Authorization": f"Bearer {token}"},
        timeout=httpx.Timeout(30.0, connect=10.0),
    ), config


def _compare(current: str, latest: str) -> int:
    def parts(value):
        return [int(part) for part in value.split(".")]

    try:
        a, b = parts(current), parts(latest)
    except ValueError:
        return -1
    width = max(len(a), len(b))
    a += [0] * (width - len(a))
    b += [0] * (width - len(b))
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


@router.get("/update/status")
def update_status() -> dict:
    """Last recorded update outcome (written by the update/health-check scripts)."""
    try:
        payload = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"status": "unknown"}
    return payload if isinstance(payload, dict) else {"status": "unknown"}


@router.post("/update/rollback", status_code=202)
def update_rollback() -> dict:
    """Restore the most recent pre-update backup (run as root via sudo)."""
    if not ROLLBACK_SCRIPT.is_file():
        raise HTTPException(status_code=501, detail="Rollback script not installed")
    try:
        subprocess.Popen(
            ["sudo", "/bin/bash", str(ROLLBACK_SCRIPT)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not start the rollback: {exc}") from exc
    return {"started": True}


@router.post("/update/apply", status_code=202)
def update_apply(payload: dict) -> dict:
    # Never trust a caller-supplied URL/checksum: re-fetch the published latest
    # from the configured server (device-token authenticated) and apply that.
    requested = str(payload.get("version") or "").strip()
    latest = update_latest()
    if not latest.get("available"):
        raise HTTPException(status_code=409, detail="No update is currently available")
    version = str(latest.get("latest_version") or "")
    url = str(latest.get("url") or "")
    sha256 = str(latest.get("sha256") or "")
    if requested and requested != version:
        raise HTTPException(status_code=409, detail="Requested version is not the published latest")
    if not _VERSION_RE.match(version) or not _SHA256_RE.match(sha256):
        raise HTTPException(status_code=400, detail="Update metadata is malformed")
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise HTTPException(status_code=400, detail="Update URL must be https")
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
