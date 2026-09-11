"""Pull server content into the kit, reporting progress to the background job."""

import hashlib
import json
import os
import socket
import tempfile
import time
from pathlib import Path
from urllib.parse import quote

import httpx

from app.core.config import get_settings
from app.services.settings_store import SettingsStore
from app.services.storage import StorageService

DEVICE_TOKEN_ENV = "FIELDKIT_DEVICE_TOKEN"
SYNC_LIBRARIES = {"data", "personal"}


def sync_error(exc: Exception) -> str:
    """Useful errors without echoing credential-bearing URLs or headers."""
    if isinstance(exc, httpx.HTTPStatusError):
        return f"Server returned HTTP {exc.response.status_code}."
    if isinstance(exc, httpx.TimeoutException):
        return "Server request timed out. Check the connection and try again."
    if isinstance(exc, httpx.HTTPError):
        return "Could not reach the server. Check the connection and server URL."
    if isinstance(exc, OSError):
        return f"Local file operation failed: {exc.strerror or type(exc).__name__}."
    if isinstance(exc, ValueError):
        return str(exc)
    return "Sync failed unexpectedly. Check the appliance service log."


class ServerSyncService:
    def __init__(self) -> None:
        self._runtime = get_settings()
        self._storage = StorageService(self._runtime)
        self._store = SettingsStore()

    def _config(self):
        return self._store.load().server_sync

    def _token(self) -> str:
        return os.environ.get(DEVICE_TOKEN_ENV) or self._config().device_token

    def _base_url(self) -> str:
        return (self._config().base_url or self._runtime.server_base_url).rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self._base_url() and self._token())

    def base_url(self) -> str:
        return self._base_url()

    def device_id(self) -> str:
        return socket.gethostname()

    def prune_enabled(self) -> bool:
        return bool(self._config().prune)

    def _managed_path(self) -> Path:
        return self._runtime.state_root / "server-sync-managed.json"

    def _load_managed(self) -> list[str]:
        try:
            data = json.loads(self._managed_path().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        return data if isinstance(data, list) else []

    def _save_managed(self, paths: list[str]) -> None:
        temporary = self._managed_path().with_suffix(".json.tmp")
        temporary.write_text(json.dumps(sorted(set(paths))), encoding="utf-8")
        os.replace(temporary, self._managed_path())

    def _prune_stale_data_files(self, manifest_paths: set[str], managed: list[str]) -> None:
        """Remove previously synced data files that left the manifest.

        Only files the sync itself downloaded (the managed list) are removed;
        user-placed files and personal content are never touched. Export copies
        are refreshed by the publishing step that follows.
        """
        remaining = []
        for relative in managed:
            if relative in manifest_paths:
                remaining.append(relative)
                continue
            try:
                target = self._storage.resolve_download("data", relative)
            except ValueError:
                continue
            try:
                if target.is_file():
                    target.unlink()
            except OSError:
                continue
        self._save_managed(remaining)

    def _client(self):
        # Freeze URL and credentials for this run; share the connection pool.
        # Downloads of mirrored files are 307-redirected to object storage;
        # httpx follows them and strips Authorization on the cross-host hop.
        return httpx.Client(
            base_url=self._base_url() + "/",
            headers={"Authorization": f"Bearer {self._token()}"},
            timeout=httpx.Timeout(120.0, connect=15.0),
            follow_redirects=True,
        )

    def get_manifest(self) -> dict:
        with self._client() as client:
            return self._get_manifest(client)

    @staticmethod
    def _get_manifest(client) -> dict:
        response = client.get("api/v1/device/manifest", timeout=120.0)
        response.raise_for_status()
        try:
            manifest = response.json()
        except ValueError as exc:
            raise ValueError("Server returned an invalid manifest.") from exc
        if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
            raise ValueError("Server returned an invalid manifest.")
        for entry in manifest["files"]:
            if (
                not isinstance(entry, dict)
                or not isinstance(entry.get("id"), str)
                or not entry["id"]
                or not isinstance(entry.get("size"), int)
                or isinstance(entry["size"], bool)
                or entry["size"] < 0
                or not isinstance(entry.get("sha256"), str)
                or len(entry["sha256"]) != 64
                or any(char not in "0123456789abcdef" for char in entry["sha256"])
            ):
                raise ValueError("Server manifest contains an invalid file entry.")
        return manifest

    def sync(self, progress=None) -> dict:
        notify = progress or (lambda update: None)
        notify({"phase": "manifest", "current_file": None, "eta_seconds": None})
        results = []
        completed_bytes = downloaded_bytes = 0
        download_seconds = 0.0
        with self._client() as client:
            manifest = self._get_manifest(client)
            entries = manifest["files"]
            total_bytes = sum(entry["size"] for entry in entries)
            notify({"total_files": len(entries), "total_bytes": total_bytes})
            prune = self.prune_enabled()
            managed = self._load_managed() if prune else []
            manifest_data_paths = {
                entry["path"]
                for entry in entries
                if (entry.get("library") or "data") == "data" and entry.get("path")
            }
            for entry in entries:
                size = entry["size"]
                name = entry.get("path") or entry.get("name") or ""
                notify({
                    "phase": "checking", "current_file": f"{entry.get('library') or 'data'}/{name}",
                    "current_file_bytes": 0, "current_file_size": size, "eta_seconds": None,
                })
                received = 0
                elapsed = 0.0

                def file_progress(byte_count, seconds):
                    nonlocal received, elapsed
                    received, elapsed = byte_count, seconds
                    speed = (downloaded_bytes + received) / max(download_seconds + elapsed, 0.001)
                    remaining = max(0, total_bytes - completed_bytes - received)
                    notify({
                        "phase": "downloading", "current_file_bytes": received,
                        "downloaded_bytes": downloaded_bytes + received,
                        "processed_bytes": completed_bytes + min(received, size),
                        "bytes_per_second": round(speed),
                        "eta_seconds": round(remaining / speed) if speed > 0 else None,
                    })

                status, error = self._sync_file(entry, client, file_progress)
                downloaded_bytes += received
                download_seconds += elapsed
                completed_bytes += size
                result = {"id": entry["id"], "name": name, "library": entry.get("library") or "data", "status": status}
                if error:
                    result["error"] = error
                results.append(result)
                if prune and result["library"] == "data" and status in {"ok", "skipped"}:
                    managed.append(entry.get("path") or "")
                notify({
                    "completed_files": len(results), "processed_bytes": completed_bytes,
                    "downloaded_bytes": downloaded_bytes,
                    "counts": self._counts(results), "eta_seconds": None,
                })

            if prune:
                self._prune_stale_data_files(manifest_data_paths, managed)
            notify({"phase": "publishing", "current_file": None, "eta_seconds": None})
            self._storage.sync_export_tree()
            notify({"phase": "reporting"})
            report_error = self._report(client, results)
        return {
            "manifest_version": manifest.get("manifest_version"), "files": results,
            "counts": self._counts(results), "report_error": report_error,
        }

    def _sync_file(self, entry, client, progress) -> tuple[str, str | None]:
        library = entry.get("library") or "data"
        if library not in SYNC_LIBRARIES:
            return "failed", "Unexpected target library."
        safe = self._safe_name(entry.get("path") or entry.get("name") or "")
        if safe is None:
            return "failed", "Manifest entry has an unsafe or missing path."
        temporary = None
        try:
            root = self._storage.library_paths()[library].resolve()
            target = (root / safe).resolve()
            if root not in target.parents:
                return "failed", "Path escapes the target library."
            if target.is_file() and target.stat().st_size == entry["size"] and self._sha256(target) == entry["sha256"]:
                return "skipped", None
            target.parent.mkdir(parents=True, exist_ok=True)
            started = time.monotonic()
            url = f"api/v1/device/files/{quote(entry['id'], safe='')}"
            last_error = None
            for attempt in (1, 2):
                received = 0
                digest = hashlib.sha256()
                started = time.monotonic()
                progress(0, 0)
                try:
                    with client.stream("GET", url) as response:
                        response.raise_for_status()
                        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".fieldkit-sync-", delete=False) as output:
                            temporary = Path(output.name)
                            for chunk in response.iter_bytes(chunk_size=64 * 1024):
                                received += len(chunk)
                                if received > entry["size"]:
                                    raise ValueError("Downloaded file exceeds its declared size.")
                                output.write(chunk)
                                digest.update(chunk)
                                progress(received, time.monotonic() - started)
                            output.flush()
                            os.fsync(output.fileno())
                    last_error = None
                    break
                except httpx.HTTPError as exc:
                    # Mirrored files live in object storage; if that fails,
                    # retry once through the server origin before giving up.
                    last_error = exc
                    if temporary is not None:
                        temporary.unlink(missing_ok=True)
                        temporary = None
                    if attempt == 2 or "source=origin" in url:
                        break
                    url += "&source=origin" if "?" in url else "?source=origin"
            if last_error is not None:
                raise last_error
            if received != entry["size"] or digest.hexdigest() != entry["sha256"]:
                return "failed", "Downloaded size or checksum does not match the manifest."
            # Publish only verified content, retaining old files on any failure.
            temporary.chmod(0o644)
            os.replace(temporary, target)
            return "ok", None
        except (httpx.HTTPError, OSError, ValueError) as exc:
            return "failed", sync_error(exc)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def _report(self, client, results) -> str | None:
        try:
            response = client.post(
                "api/v1/device/sync-results",
                json={"device_id": self.device_id(), "files": results}, timeout=30.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return sync_error(exc)
        return None

    @staticmethod
    def _counts(results):
        return {status: sum(result["status"] == status for result in results) for status in ("ok", "skipped", "failed")}

    @staticmethod
    def _safe_name(name: str) -> str | None:
        if not isinstance(name, str) or not name or "\x00" in name or name.startswith("/") or ".." in name.split("/"):
            return None
        return name

    @staticmethod
    def _sha256(path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
