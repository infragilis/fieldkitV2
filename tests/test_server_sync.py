import hashlib

import httpx
import pytest

from app.core.config import RuntimeSettings
from app.services import server_sync as ss_module


def test_safe_name_rejects_traversal():
    assert ss_module.ServerSyncService._safe_name("kits/netapp.txt") == "kits/netapp.txt"
    assert ss_module.ServerSyncService._safe_name("../etc/passwd") is None
    assert ss_module.ServerSyncService._safe_name("/etc/passwd") is None
    assert ss_module.ServerSyncService._safe_name("") is None


def test_configured_requires_token_and_url(monkeypatch, tmp_path):
    settings = RuntimeSettings(content_root=tmp_path / "content", state_root=tmp_path / "state")
    monkeypatch.setattr(ss_module, "get_settings", lambda: settings)
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
