import hashlib
import json
import threading
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import RuntimeSettings
from app.services import server_sync as ss_module
from app.services import settings_store
from app.services.server_sync_job import ServerSyncJob


def test_safe_name_rejects_traversal():
    assert ss_module.ServerSyncService._safe_name("kits/netapp.txt") == "kits/netapp.txt"
    assert ss_module.ServerSyncService._safe_name("../etc/passwd") is None
    assert ss_module.ServerSyncService._safe_name("/etc/passwd") is None
    assert ss_module.ServerSyncService._safe_name("") is None


def test_configured_requires_token_and_url(monkeypatch, tmp_path):
    settings = RuntimeSettings(content_root=tmp_path / "content", state_root=tmp_path / "state")
    monkeypatch.setattr(ss_module, "get_settings", lambda: settings)
    monkeypatch.setattr(settings_store, "get_settings", lambda: settings)
    monkeypatch.setenv(ss_module.DEVICE_TOKEN_ENV, "token")

    assert ss_module.ServerSyncService().configured is True

    monkeypatch.delenv(ss_module.DEVICE_TOKEN_ENV)
    assert ss_module.ServerSyncService().configured is False


def _service(monkeypatch, tmp_path, manifest, content):
    settings = RuntimeSettings(
        content_root=tmp_path / "content",
        state_root=tmp_path / "state",
        server_base_url="https://example.com",
    )
    monkeypatch.setattr(ss_module, "get_settings", lambda: settings)
    monkeypatch.setattr(settings_store, "get_settings", lambda: settings)
    monkeypatch.setattr(ss_module.StorageService, "_detect_usb_mount", lambda self: None)
    monkeypatch.setenv(ss_module.DEVICE_TOKEN_ENV, "token")

    file_id = hashlib.sha256(content).hexdigest()

    def handler(request):
        if request.url.path == "/api/v1/device/manifest":
            return httpx.Response(200, json=manifest)
        if request.url.path == f"/api/v1/device/files/{file_id}":
            return httpx.Response(200, content=content)
        if request.url.path == "/api/v1/device/sync-results":
            return httpx.Response(202, json={"accepted": True})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client
    monkeypatch.setattr(
        ss_module.httpx,
        "Client",
        lambda *args, **kwargs: real_client(transport=transport, *args, **kwargs),
    )
    return ss_module.ServerSyncService()


def test_sync_downloads_new_file(monkeypatch, tmp_path):
    content = b"hello fieldkit\n"
    sha = hashlib.sha256(content).hexdigest()
    manifest = {
        "manifest_version": 1,
        "files": [{"id": sha, "name": "kits/hello.txt", "size": len(content), "sha256": sha}],
    }
    service = _service(monkeypatch, tmp_path, manifest, content)

    result = service.sync()

    assert result["files"][0]["status"] == "ok"
    data_root = service._storage.library_paths()["data"]
    assert (data_root / "kits" / "hello.txt").read_bytes() == content


def test_sync_skips_unchanged_file(monkeypatch, tmp_path):
    content = b"already there\n"
    sha = hashlib.sha256(content).hexdigest()
    manifest = {
        "manifest_version": 1,
        "files": [{"id": sha, "name": "firmware.bin", "size": len(content), "sha256": sha}],
    }
    service = _service(monkeypatch, tmp_path, manifest, content)
    data_root = service._storage.library_paths()["data"]
    data_root.mkdir(parents=True, exist_ok=True)
    (data_root / "firmware.bin").write_bytes(content)

    result = service.sync()

    assert result["files"][0]["status"] == "skipped"


def test_sync_maps_library_from_manifest(monkeypatch, tmp_path):
    content = b"personal note\n"
    sha = hashlib.sha256(content).hexdigest()
    manifest = {
        "manifest_version": 1,
        "files": [
            {"id": sha, "name": "personal/demo/note.txt", "path": "note.txt", "library": "personal", "size": len(content), "sha256": sha},
        ],
    }
    service = _service(monkeypatch, tmp_path, manifest, content)

    result = service.sync()

    assert result["files"][0]["status"] == "ok"
    personal_root = service._storage.library_paths()["personal"]
    assert (personal_root / "note.txt").read_bytes() == content
    data_root = service._storage.library_paths()["data"]
    assert not (data_root / "note.txt").exists()


def test_sync_maps_data_path_to_data_library(monkeypatch, tmp_path):
    content = b"shared\n"
    sha = hashlib.sha256(content).hexdigest()
    manifest = {
        "manifest_version": 1,
        "files": [
            {"id": sha, "name": "data/kits/x.txt", "path": "kits/x.txt", "library": "data", "size": len(content), "sha256": sha},
        ],
    }
    service = _service(monkeypatch, tmp_path, manifest, content)

    result = service.sync()

    assert result["files"][0]["status"] == "ok"
    data_root = service._storage.library_paths()["data"]
    assert (data_root / "kits" / "x.txt").read_bytes() == content


def test_sync_streams_progress_and_publishes_vendor_file(monkeypatch, tmp_path):
    content = b"x" * (128 * 1024)
    sha = hashlib.sha256(content).hexdigest()
    manifest = {"manifest_version": 1, "files": [{"id": sha, "path": "ontap/image.bin", "library": "data", "size": len(content), "sha256": sha}]}
    service = _service(monkeypatch, tmp_path, manifest, content)
    updates = []

    result = service.sync(progress=updates.append)

    assert result["counts"] == {"ok": 1, "skipped": 0, "failed": 0}
    downloads = [update for update in updates if update.get("phase") == "downloading"]
    assert any(0 < update["current_file_bytes"] < len(content) for update in downloads)
    assert any(update["eta_seconds"] is not None for update in downloads)
    assert downloads[-1]["downloaded_bytes"] == len(content)
    assert (service._storage.export_root() / "data/ontap/image.bin").read_bytes() == content
    assert "error" not in result["files"][0]


def test_bad_checksum_keeps_previous_file_and_cleans_temporary(monkeypatch, tmp_path):
    content = b"oops"
    manifest = {"files": [{"id": hashlib.sha256(content).hexdigest(), "path": "ontap/image.bin", "size": 4, "sha256": hashlib.sha256(b"good").hexdigest()}]}
    service = _service(monkeypatch, tmp_path, manifest, content)
    target = service._storage.library_paths()["data"] / "ontap/image.bin"
    target.write_bytes(b"previous")

    result = service.sync()

    assert result["counts"]["failed"] == 1
    assert target.read_bytes() == b"previous"
    assert not list(target.parent.glob(".fieldkit-sync-*"))


@pytest.mark.parametrize("size", [1, 100])
def test_wrong_download_size_is_reported(monkeypatch, tmp_path, size):
    content = b"actual"
    sha = hashlib.sha256(content).hexdigest()
    service = _service(monkeypatch, tmp_path, {"files": [{"id": sha, "path": "bes/file.bin", "size": size, "sha256": sha}]}, content)
    assert service.sync()["counts"]["failed"] == 1
    assert not (service._storage.library_paths()["data"] / "bes/file.bin").exists()


@pytest.mark.parametrize("entry", [{}, {"id": "x", "size": -1, "sha256": "0" * 64}, {"id": "x", "size": 3, "sha256": "invalid"}])
def test_malformed_manifest_fails_cleanly(monkeypatch, tmp_path, entry):
    service = _service(monkeypatch, tmp_path, {"files": [entry]}, b"")
    with pytest.raises(ValueError, match="invalid file entry"):
        service.sync()


def test_result_report_failure_is_visible(monkeypatch, tmp_path):
    service = _service(monkeypatch, tmp_path, {"files": []}, b"")
    class DeniedClient:
        def post(self, *args, **kwargs):
            return httpx.Response(401, request=httpx.Request("POST", "https://example.com"))
    assert service._report(DeniedClient(), []) == "Server returned HTTP 401."


def test_standard_vendor_directories_are_created_without_moving_files(monkeypatch, tmp_path):
    service = _service(monkeypatch, tmp_path, {"files": []}, b"")
    root = service._storage.library_paths()["data"]
    (root / "existing.txt").write_text("keep")
    ss_module.StorageService(service._runtime)
    assert all((root / name).is_dir() for name in ("cisco", "ontap", "brocade", "efos", "nvidia"))
    assert (root / "existing.txt").read_text() == "keep"


class FakeSyncService:
    configured = True

    def __init__(self, tmp_path):
        self._runtime = RuntimeSettings(state_root=tmp_path)
        self.entered = threading.Event()
        self.release = threading.Event()

    def base_url(self):
        return "https://example.com"

    def device_id(self):
        return "demo-kit"

    def sync(self, progress):
        progress({"phase": "downloading", "downloaded_bytes": 64, "eta_seconds": 4})
        self.entered.set()
        assert self.release.wait(3)
        return {"files": [], "counts": {"ok": 1, "skipped": 2, "failed": 0}, "report_error": None}


def test_background_api_returns_immediately_and_deduplicates(monkeypatch, tmp_path):
    from app.api.routes import server_sync as routes
    from app.main import app
    service = FakeSyncService(tmp_path)
    job = ServerSyncJob(service)
    monkeypatch.setattr(routes, "service", service)
    monkeypatch.setattr(routes, "job", job)
    client = TestClient(app)
    try:
        first = client.post("/api/server-sync/sync")
        assert first.status_code == 202
        assert first.json()["started"]
        assert service.entered.wait(1)
        second = client.post("/api/server-sync/sync?trigger=scheduled")
        assert second.status_code == 202
        assert not second.json()["started"]
        current = client.get("/api/server-sync/status").json()
        assert current["running"]
        assert current["current_sync"]["downloaded_bytes"] == 64
        assert current["current_sync"]["eta_seconds"] == 4
    finally:
        service.release.set()
        job._thread.join(3)
    state = job.status()
    assert not state["running"]
    assert state["last_sync"]["outcome"] == "success"
    assert state["last_sync"]["trigger"] == "manual"
    assert state["last_success_at"]
    restored = ServerSyncJob(service).status()
    assert restored["last_sync"] == state["last_sync"]


def test_job_records_offline_failure_and_can_retry(monkeypatch, tmp_path):
    service = FakeSyncService(tmp_path)
    def offline(progress):
        raise httpx.ConnectError("private connection detail")
    monkeypatch.setattr(service, "sync", offline)
    job = ServerSyncJob(service)
    assert job.start("scheduled")
    job._thread.join(3)
    state = job.status()
    assert state["last_sync"]["outcome"] == "failed"
    assert state["last_sync"]["trigger"] == "scheduled"
    assert "private connection detail" not in state["last_sync"]["error"]
    assert job.start()
    job._thread.join(3)


def test_job_marks_unfinished_run_interrupted_after_restart(tmp_path):
    service = FakeSyncService(tmp_path)
    path = tmp_path / "server-sync-status.json"
    path.write_text(json.dumps({"current_sync": {"started_at": "2026-01-01T00:00:00+00:00", "trigger": "scheduled"}}))
    job = ServerSyncJob(service)
    assert job.status()["last_sync"]["outcome"] == "interrupted"
    assert not job.status()["running"]


def test_unconfigured_scheduled_run_is_skipped(monkeypatch, tmp_path):
    from app.api.routes import server_sync as routes
    from app.main import app
    service = FakeSyncService(tmp_path)
    service.configured = False
    monkeypatch.setattr(routes, "service", service)
    monkeypatch.setattr(routes, "job", ServerSyncJob(service))
    client = TestClient(app)
    assert client.post("/api/server-sync/sync").status_code == 400
    scheduled = client.post("/api/server-sync/sync?trigger=scheduled")
    assert scheduled.status_code == 202
    assert scheduled.json()["reason"] == "not_configured"
    assert not scheduled.json()["running"]


def test_unrelated_settings_save_preserves_sync_token(monkeypatch, tmp_path):
    from app.api.routes import settings as routes
    from app.core.models import AppSettingsPayload
    from app.main import app
    store = settings_store.SettingsStore()
    store.path = tmp_path / "settings.json"
    original = AppSettingsPayload()
    original.server_sync.device_token = "synthetic-token"
    store.save(original)
    monkeypatch.setattr(routes, "store", store)
    payload = original.model_dump(exclude={"server_sync"})
    payload["hostname"] = "demo-kit"
    assert TestClient(app).put("/api/settings", json=payload).status_code == 200
    assert store.load().server_sync.device_token == "synthetic-token"


def test_blank_config_token_keeps_saved_token(monkeypatch, tmp_path):
    from app.api.routes import server_sync as routes
    from app.core.models import AppSettingsPayload
    from app.main import app
    store = settings_store.SettingsStore()
    store.path = tmp_path / "settings.json"
    original = AppSettingsPayload()
    original.server_sync.device_token = "synthetic-token"
    store.save(original)
    service = FakeSyncService(tmp_path)
    monkeypatch.setattr(routes, "store", store)
    monkeypatch.setattr(routes, "service", service)
    monkeypatch.setattr(routes, "job", ServerSyncJob(service))
    response = TestClient(app).put("/api/server-sync/config", json={"base_url": "https://example.com", "device_token": ""})
    assert response.status_code == 200
    assert store.load().server_sync.device_token == "synthetic-token"


def test_timer_uses_boot_delay_and_hourly_interval():
    timer = Path("deploy/systemd/fieldkit-server-sync.timer").read_text()
    assert "OnBootSec=10min" in timer
    assert "OnUnitActiveSec=1h" in timer


def test_vendor_folder_api_with_relative_runtime_roots(monkeypatch, tmp_path):
    from app.api.routes import files as routes
    from app.main import app
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(ss_module.StorageService, "_detect_usb_mount", lambda self: None)
    storage = ss_module.StorageService(RuntimeSettings(content_root=Path("content"), state_root=Path("state")))
    (storage.library_paths()["data"] / "ontap/image.bin").write_bytes(b"image")
    monkeypatch.setattr(routes, "storage_service", storage)
    response = TestClient(app).get("/api/files", params={"library": "data", "path": "ontap"})
    assert response.status_code == 200
    assert response.json()["path"] == "ontap"
    assert response.json()["items"][0]["path"] == "ontap/image.bin"


def test_sync_follows_s3_redirect_without_forwarding_token(monkeypatch, tmp_path):
    content = b"mirrored vendor image"
    sha = hashlib.sha256(content).hexdigest()
    manifest = {
        "manifest_version": 1,
        "files": [{"id": sha, "name": "data/ontap/image.bin", "path": "ontap/image.bin", "library": "data", "size": len(content), "sha256": sha, "storage": "s3"}],
    }
    seen_authorization = []

    def handler(request):
        seen_authorization.append(request.headers.get("authorization"))
        if request.url.path == "/api/v1/device/manifest":
            return httpx.Response(200, json=manifest)
        if request.url.host == "cdn.example.com":
            assert request.headers.get("authorization") is None
            return httpx.Response(200, content=content)
        if request.url.path == "/api/v1/device/files/{}".format(sha):
            return httpx.Response(307, headers={"Location": "https://cdn.example.com/data/ontap/image.bin"})
        if request.url.path == "/api/v1/device/sync-results":
            return httpx.Response(202, json={"accepted": True})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client
    monkeypatch.setattr(
        ss_module.httpx,
        "Client",
        lambda *args, **kwargs: real_client(transport=transport, *args, **kwargs),
    )
    settings = RuntimeSettings(
        content_root=tmp_path / "content",
        state_root=tmp_path / "state",
        server_base_url="https://example.com",
    )
    monkeypatch.setattr(ss_module, "get_settings", lambda: settings)
    monkeypatch.setattr(settings_store, "get_settings", lambda: settings)
    monkeypatch.setattr(ss_module.StorageService, "_detect_usb_mount", lambda self: None)
    monkeypatch.setenv(ss_module.DEVICE_TOKEN_ENV, "token")
    service = ss_module.ServerSyncService()

    result = service.sync()

    assert result["files"][0]["status"] == "ok"
    data_root = service._storage.library_paths()["data"]
    assert (data_root / "ontap" / "image.bin").read_bytes() == content
    assert "Bearer token" in seen_authorization
    assert all(header is None or "cdn.example.com" not in str(header) for header in seen_authorization[1:])


def test_sync_retries_mirrored_file_via_origin(monkeypatch, tmp_path):
    content = b"fallback content"
    sha = hashlib.sha256(content).hexdigest()
    manifest = {
        "manifest_version": 1,
        "files": [{"id": sha, "name": "data/cisco/image.bin", "path": "cisco/image.bin", "library": "data", "size": len(content), "sha256": sha, "storage": "s3"}],
    }
    origin_attempts = []

    def handler(request):
        if request.url.path == "/api/v1/device/manifest":
            return httpx.Response(200, json=manifest)
        if request.url.host == "cdn.example.com":
            return httpx.Response(503)
        if request.url.path == "/api/v1/device/files/{}".format(sha):
            origin_attempts.append(request.url.query.decode())
            if request.url.query.decode() != "source=origin":
                return httpx.Response(307, headers={"Location": "https://cdn.example.com/data/cisco/image.bin"})
            return httpx.Response(200, content=content)
        if request.url.path == "/api/v1/device/sync-results":
            return httpx.Response(202, json={"accepted": True})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client
    monkeypatch.setattr(
        ss_module.httpx,
        "Client",
        lambda *args, **kwargs: real_client(transport=transport, *args, **kwargs),
    )
    settings = RuntimeSettings(
        content_root=tmp_path / "content",
        state_root=tmp_path / "state",
        server_base_url="https://example.com",
    )
    monkeypatch.setattr(ss_module, "get_settings", lambda: settings)
    monkeypatch.setattr(settings_store, "get_settings", lambda: settings)
    monkeypatch.setattr(ss_module.StorageService, "_detect_usb_mount", lambda self: None)
    monkeypatch.setenv(ss_module.DEVICE_TOKEN_ENV, "token")
    service = ss_module.ServerSyncService()

    result = service.sync()

    assert result["files"][0]["status"] == "ok"
    assert origin_attempts == ["", "source=origin"]
    data_root = service._storage.library_paths()["data"]
    assert (data_root / "cisco" / "image.bin").read_bytes() == content
