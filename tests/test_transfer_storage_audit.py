from pathlib import Path
from types import SimpleNamespace

import pytest

from app.core.config import RuntimeSettings
from app.services.serial import SerialService
from app.services.storage import StorageService
from app.services.transfers import TransferService


def test_export_rejects_symlink_file_and_directory(tmp_path):
    settings = RuntimeSettings(content_root=tmp_path / "content", state_root=tmp_path / "state")
    service = StorageService(settings)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret").write_text("secret")
    (service.library_paths()["data"] / "link").symlink_to(outside / "secret")
    with pytest.raises(ValueError):
        service.sync_export_tree()
    (service.library_paths()["data"] / "link").unlink()
    (service.library_paths()["data"] / "folder").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        service.sync_export_tree()
    assert not (service.export_root() / "data" / "folder" / "secret").exists()


def test_transfer_http_mode_and_status(monkeypatch):
    service = TransferService()
    calls = []

    def run(command, env=None):
        calls.append(command)
        if command[:1] == ["ss"]:
            return SimpleNamespace(ok=True, stdout="LISTEN 0 128 0.0.0.0:80 0.0.0.0:*", stderr="")
        if command[:1] == ["curl"]:
            return SimpleNamespace(ok=True, stdout="404", stderr="")
        return SimpleNamespace(ok=True, stdout="", stderr="")

    monkeypatch.setattr(service._runner, "run", run)
    assert service._http_export_preview(False).endswith(" disable")
    result = service._apply_http_export(False)
    assert calls[-1][-1] == "disable"
    assert result.ok
    assert calls[-1][0:2] == ["sudo", "-n"]  # apply remains privileged
    monkeypatch.setattr(service, "_read_text", lambda path: "listen 80;\nlocation ^~ /fieldkit { return 404; }")
    assert service._http_export_status(False)["active"] is False
    assert not any(command[:2] == ["sudo", "-n"] and "ss" in command for command in calls)
    assert any(command[:1] == ["curl"] for command in calls)


def test_transfer_status_uses_live_probe_when_config_is_stale(monkeypatch):
    service = TransferService()
    monkeypatch.setattr(service, "_read_text", lambda path: "listen 80; proxy_pass http://127.0.0.1:8000;")
    monkeypatch.setattr(
        service._runner,
        "run",
        lambda command, env=None: SimpleNamespace(
            ok=True,
            stdout="LISTEN 0 128 0.0.0.0:80 0.0.0.0:*" if command[:1] == ["ss"] else "404",
            stderr="",
        ),
    )
    assert service._http_export_status(True)["active"] is False

    monkeypatch.setattr(
        service._runner,
        "run",
        lambda command, env=None: SimpleNamespace(
            ok=True,
            stdout="LISTEN 0 128 0.0.0.0:80 0.0.0.0:*" if command[:1] == ["ss"] else "200",
            stderr="",
        ),
    )
    monkeypatch.setattr(service, "_read_text", lambda path: "listen 80; location ^~ /fieldkit { return 404; }")
    assert service._http_export_status(False)["active"] is True


def test_serial_log_directory_and_file_modes(tmp_path):
    service = SerialService.__new__(SerialService)
    service._log_root = tmp_path / "logs"
    profile = SimpleNamespace(label="Console", device_hint="/dev/ttyUSB0")
    first = service._create_session_log_path(profile)
    second = service._create_session_log_path(profile)
    assert service._log_root.stat().st_mode & 0o777 == 0o700
    assert first.stat().st_mode & 0o777 == 0o600
    assert second != first


def test_transfer_install_script_keeps_read_only_services():
    script = Path("scripts/install_transfer_services.sh").read_text()
    assert "--create" not in script
    assert "write_enable=NO" in script
