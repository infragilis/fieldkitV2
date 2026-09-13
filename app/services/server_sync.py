"""Pull server content into the kit, reporting progress to the background job."""

import hashlib
import json
import os
import shutil
import socket
import tempfile
import time
import uuid
from pathlib import Path
from urllib.parse import quote, urlsplit

import httpx

from app.core.config import get_settings
from app.services.settings_store import SettingsStore
from app.services.storage import StorageService

DEVICE_TOKEN_ENV = "FIELDKIT_DEVICE_TOKEN"
SYNC_LIBRARIES = {"data", "personal"}
DISK_MARGIN_BYTES = 256 * 1024**2


def human_bytes(value: int) -> str:
    if value <= 0:
        return "0 B"
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024 or unit == "GiB":
            return f"{value:.1f} {unit}"
        value /= 1024


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
        self._hash_cache: dict[str, dict] | None = None
        self._hash_cache_dirty = False

    def _hash_cache_path(self) -> Path:
        return self._runtime.state_root / "sync-hash-cache.json"

    def _load_hash_cache(self) -> dict[str, dict]:
        if self._hash_cache is None:
            try:
                data = json.loads(self._hash_cache_path().read_text(encoding="utf-8"))
                self._hash_cache = data if isinstance(data, dict) else {}
            except (OSError, ValueError):
                self._hash_cache = {}
        return self._hash_cache

    def _save_hash_cache(self) -> None:
        if not self._hash_cache_dirty or self._hash_cache is None:
            return
        # Keep only entries for files that still exist so the cache cannot grow
        # without bound as files come and go.
        live = {key: value for key, value in self._hash_cache.items() if Path(key).is_file()}
        self._hash_cache = live
        temporary = self._hash_cache_path().with_suffix(".json.tmp")
        try:
            self._hash_cache_path().parent.mkdir(parents=True, exist_ok=True)
            temporary.write_text(json.dumps(live), encoding="utf-8")
            os.replace(temporary, self._hash_cache_path())
        except OSError:
            temporary.unlink(missing_ok=True)
            return
        self._hash_cache_dirty = False

    def _remember_hash(self, path: Path, digest: str) -> None:
        try:
            stat = path.stat()
        except OSError:
            return
        self._load_hash_cache()[str(path)] = {
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "sha256": digest,
        }
        self._hash_cache_dirty = True

    def _config(self):
        return self._store.load().server_sync

    def _token(self) -> str:
        configured = self._config()
        return self._token_for(configured)

    def _token_for(self, configured) -> str:
        environment_token = os.environ.get(DEVICE_TOKEN_ENV)
        # The environment override is provisioned for the runtime's trusted
        # server. Never carry it over when an operator changes the origin.
        if environment_token and self.origins_match(self._base_url_for(configured), self._runtime.server_base_url):
            return environment_token
        return configured.device_token

    def _base_url(self) -> str:
        return self._base_url_for(self._config())

    def _base_url_for(self, configured) -> str:
        return (configured.base_url or self._runtime.server_base_url).rstrip("/")

    def connection_config(self) -> tuple[str, str]:
        """Return one consistent URL/token snapshot for an outbound client."""
        configured = self._config()
        return self._base_url_for(configured), self._token_for(configured)

    @staticmethod
    def _origin(value: str) -> tuple[str, str, int] | None:
        try:
            parsed = urlsplit(value.strip())
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                return None
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            return parsed.scheme.lower(), parsed.hostname.lower().rstrip("."), port
        except ValueError:
            return None

    @classmethod
    def origins_match(cls, left: str, right: str) -> bool:
        return cls._origin(left) is not None and cls._origin(left) == cls._origin(right)

    @property
    def configured(self) -> bool:
        return bool(self._base_url() and self._token())

    def base_url(self) -> str:
        return self._base_url()

    def device_id(self) -> str:
        """Stable per-kit id, persisted so it survives hostname reuse/changes."""
        path = self._runtime.state_root / "device-id"
        try:
            value = path.read_text(encoding="utf-8").strip()
            if value:
                return value
        except OSError:
            pass
        value = uuid.uuid4().hex
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value, encoding="utf-8")
        except OSError:
            pass
        return value

    def device_label(self) -> str:
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

    def _manifest_target(self, entry: dict) -> Path | None:
        library = entry.get("library") or "data"
        relative = entry.get("path") or entry.get("name") or ""
        try:
            return self._storage.resolve_download(library, relative)
        except ValueError:
            return None

    def _mirror_target(self, entry: dict) -> Path | None:
        library = entry.get("library") or "data"
        relative = entry.get("path") or entry.get("name") or ""
        try:
            return self._storage.export_root() / library / relative
        except (OSError, ValueError):
            return None

    def _plan_entries(self, entries: list[dict]) -> dict[str, str]:
        """Decide skip vs download once, hashing present files a single time."""
        plan: dict[str, str] = {}
        for entry in entries:
            target = self._manifest_target(entry)
            if target is not None and target.is_file() \
                    and target.stat().st_size == entry["size"] \
                    and self._sha256(target) == entry["sha256"]:
                plan[entry["id"]] = "skip"
            else:
                plan[entry["id"]] = "download"
        return plan

    def _check_disk_space(self, entries: list[dict], plan: dict[str, str]) -> None:
        """Refuse to start when the library plus its export mirror cannot fit.

        Runs after pruning, so a tightened server-side sync window can free
        space and let the next sync recover a full kit.
        """
        library_needed = 0
        mirror_needed = 0
        largest = 0
        for entry in entries:
            size = entry["size"]
            if plan.get(entry["id"]) == "download":
                library_needed += size
                largest = max(largest, size)
            mirror = self._mirror_target(entry)
            if mirror is None or not mirror.is_file() or mirror.stat().st_size != size:
                mirror_needed += size
        base = library_needed + mirror_needed + largest
        if base == 0:
            return
        required = base + DISK_MARGIN_BYTES
        anchor = self._storage.library_paths()["data"]
        free = shutil.disk_usage(anchor.parent).free
        if free < required:
            raise ValueError(
                "Not enough disk space: this sync needs about "
                f"{human_bytes(required)} free, but only {human_bytes(free)} is "
                "available. Reduce the sync set on the server (Data page) and "
                "try again."
            )

    def _client(self):
        # Freeze URL and credentials for this run; share the connection pool.
        # Downloads of mirrored files are 307-redirected to object storage;
        # httpx follows them and strips Authorization on the cross-host hop.
        base_url, token = self.connection_config()
        return httpx.Client(
            base_url=base_url + "/",
            headers={"Authorization": f"Bearer {token}"},
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
        ids: set[str] = set()
        destinations: set[tuple[str, str]] = set()
        for entry in manifest["files"]:
            entry_id = entry["id"]
            library = entry.get("library") or "data"
            path = entry.get("path") or entry.get("name") or ""
            if entry_id in ids:
                raise ValueError("Server manifest contains duplicate file IDs.")
            destination = (library, path)
            if destination in destinations:
                raise ValueError("Server manifest contains duplicate file destinations.")
            ids.add(entry_id)
            destinations.add(destination)
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
            if prune:
                self._prune_stale_data_files(manifest_data_paths, managed)
            plan = self._plan_entries(entries)
            self._save_hash_cache()
            self._check_disk_space(entries, plan)
            for entry in entries:
                if plan.get(entry["id"]) == "skip":
                    result = {
                        "id": entry["id"],
                        "name": entry.get("path") or entry.get("name") or "",
                        "library": entry.get("library") or "data",
                        "status": "skipped",
                        "size": entry.get("size") or 0,
                    }
                    results.append(result)
                    notify({
                        "completed_files": len(results),
                        "counts": self._counts(results), "eta_seconds": None,
                    })
                    if prune and result["library"] == "data":
                        managed.append(entry.get("path") or "")
                    continue
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
                result = {"id": entry["id"], "name": name, "library": entry.get("library") or "data", "status": status, "size": entry.get("size") or 0}
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
            self._save_hash_cache()
            notify({"phase": "reporting"})
            report_error = self._report(client, self._report_inventory(entries, results))
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
            self._remember_hash(target, entry["sha256"])
            return "ok", None
        except (httpx.HTTPError, OSError, ValueError) as exc:
            return "failed", sync_error(exc)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def _report_inventory(self, entries: list[dict], results: list[dict]) -> list[dict]:
        """Actual on-disk contents of the synced libraries, with failures overlaid.

        This is the reliable source of truth for the server's "what's on the
        kit" view: it reflects reality even when a sync failed, a file was
        removed, or content was added outside a sync. Present files are `ok`;
        this run's failed downloads are surfaced even when the file is absent.
        """
        manifest_size: dict[tuple[str, str], int] = {}
        for entry in entries:
            key = (entry.get("library") or "data", entry.get("path") or entry.get("name") or "")
            manifest_size[key] = int(entry.get("size") or 0)
        failed: dict[tuple[str, str], str | None] = {}
        for result in results:
            if result.get("status") == "failed":
                failed[(result.get("library") or "data", result.get("name") or "")] = result.get("error")

        inventory: dict[tuple[str, str], dict] = {}
        for library in ("data", "personal"):
            root = self._storage.library_paths().get(library)
            if root is None or not root.is_dir():
                continue
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                relative = path.relative_to(root).as_posix()
                if any(part.startswith(".") for part in relative.split("/")):
                    continue
                key = (library, relative)
                try:
                    size = path.stat().st_size
                except OSError:
                    continue
                item = {"name": relative, "library": library, "status": "ok", "size": size}
                if key in failed:
                    item["status"] = "failed"
                    if failed[key]:
                        item["error"] = failed[key]
                inventory[key] = item

        for key, error in failed.items():
            if key in inventory:
                continue
            item = {"name": key[1], "library": key[0], "status": "failed", "size": manifest_size.get(key, 0)}
            if error:
                item["error"] = error
            inventory[key] = item

        return list(inventory.values())[:10000]

    def _report(self, client, results) -> str | None:
        try:
            response = client.post(
                "api/v1/device/sync-results",
                json={"device_id": self.device_id(), "device_label": self.device_label(), "files": results}, timeout=30.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return sync_error(exc)
        return None

    def report_requested(self) -> bool:
        """True when the server has asked this kit to post a fresh inventory."""
        if not self.configured:
            return False
        with self._client() as client:
            response = client.get("api/v1/device/report-requested", timeout=15.0)
            response.raise_for_status()
            return bool(response.json().get("requested"))

    def report_now(self) -> str | None:
        """Post an inventory-only report (no manifest fetch or downloads)."""
        if not self.configured:
            return "not configured"
        with self._client() as client:
            return self._report(client, self._report_inventory([], []))

    @staticmethod
    def _counts(results):
        return {status: sum(result["status"] == status for result in results) for status in ("ok", "skipped", "failed")}

    @staticmethod
    def _safe_name(name: str) -> str | None:
        if not isinstance(name, str) or not name or "\x00" in name or name.startswith("/") or ".." in name.split("/"):
            return None
        return name

    def _sha256(self, path: Path) -> str:
        """SHA-256 with a size+mtime cache so unchanged files are never re-read."""
        try:
            stat = path.stat()
        except OSError:
            return ""
        cache = self._load_hash_cache()
        cached = cache.get(str(path))
        if cached and cached.get("size") == stat.st_size and cached.get("mtime_ns") == stat.st_mtime_ns:
            return cached.get("sha256", "")
        digest = self._hash_file(path)
        cache[str(path)] = {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": digest}
        self._hash_cache_dirty = True
        return digest

    @staticmethod
    def _hash_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
