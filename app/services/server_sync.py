"""Synchronize content from the Fieldkit server down to the appliance.

Implements the public device API contract (`docs/fieldkit-server-api.openapi.yaml`):
manifest -> files -> sync-results. The server base URL is configurable and the
device token is read from the environment at runtime (never committed or
persisted in settings).
"""

import hashlib
import os
import socket

import httpx

from app.core.config import get_settings
from app.services.storage import StorageService

DEVICE_TOKEN_ENV = "FIELDKIT_DEVICE_TOKEN"


class ServerSyncService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._storage = StorageService(self._settings)
        self._token = os.environ.get(DEVICE_TOKEN_ENV, "")

    @property
    def configured(self) -> bool:
        return bool(self._settings.server_base_url and self._token)

    def base_url(self) -> str:
        return self._settings.server_base_url.rstrip("/")

    def device_id(self) -> str:
        return socket.gethostname()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    def get_manifest(self) -> dict:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{self.base_url()}/api/v1/device/manifest", headers=self._headers())
            response.raise_for_status()
            return response.json()

    def sync(self) -> dict:
        manifest = self.get_manifest()
        results = []
        for entry in manifest.get("files", []):
            status, error = self._sync_file(entry)
            results.append({"id": entry["id"], "name": entry.get("name"), "status": status, "error": error})
        self._report(results)
        return {"manifest_version": manifest.get("manifest_version"), "files": results}

    def _sync_file(self, entry: dict) -> tuple[str, str | None]:
        name = self._safe_name(entry.get("name", ""))
        if name is None:
            return "failed", "manifest entry has an unsafe or missing name"
        data_root = self._storage.library_paths()["data"].resolve()
        target = (data_root / name).resolve()
        if data_root not in target.parents:
            return "failed", "path escapes the data library"
        if target.is_file() and self._sha256(target) == entry.get("sha256"):
            return "skipped", None
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.get(
                    f"{self.base_url()}/api/v1/device/files/{entry['id']}", headers=self._headers()
                )
                response.raise_for_status()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(response.content)
        except httpx.HTTPError as exc:
            return "failed", str(exc)
        if self._sha256(target) != entry.get("sha256"):
            return "failed", "checksum mismatch after download"
        return "ok", None

    def _report(self, results: list[dict]) -> None:
        try:
            with httpx.Client(timeout=30.0) as client:
                client.post(
                    f"{self.base_url()}/api/v1/device/sync-results",
                    headers=self._headers(),
                    json={"device_id": self.device_id(), "files": results},
                )
        except httpx.HTTPError:
            pass

    @staticmethod
    def _safe_name(name: str) -> str | None:
        if not name or name.startswith("/") or ".." in name.split("/"):
            return None
        return name

    @staticmethod
    def _sha256(path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
