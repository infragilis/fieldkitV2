from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.core.config import RuntimeSettings
from app.services.serial import SerialService
from app.services.storage import StorageService
from app.services.transfers import TransferService


client = TestClient(app)


def test_system_status():
    response = client.get("/api/system/status")
    assert response.status_code == 200
    assert response.json()["hostname"] == "fieldkit"


def test_file_libraries():
    response = client.get("/api/files/libraries")
    assert response.status_code == 200
    names = {entry["name"] for entry in response.json()["libraries"]}
    assert {"data", "personal", "usb", "serial-logs"} <= names


def test_delete_personal_file():
    response = client.post(
        "/api/files/upload",
        files={"file": ("delete-me.txt", b"content", "text/plain")},
    )
    assert response.status_code == 200

    delete_response = client.delete("/api/files", params={"library": "personal", "path": "delete-me.txt"})
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True


def test_upload_to_usb_allowed():
    response = client.post(
        "/api/files/upload",
        params={"library": "usb"},
        files={"file": ("usb-test.txt", b"content", "text/plain")},
    )
    assert response.status_code == 200
    assert response.json()["library"] == "usb"


def test_duplicate_upload_returns_conflict():
    first = client.post(
        "/api/files/upload",
        params={"library": "personal"},
        files={"file": ("duplicate.txt", b"one", "text/plain")},
    )
    assert first.status_code == 200

    second = client.post(
        "/api/files/upload",
        params={"library": "personal"},
        files={"file": ("duplicate.txt", b"two", "text/plain")},
    )
    assert second.status_code == 409
    assert "File already exists" in second.json()["detail"]


def test_upload_to_data_disallowed():
    response = client.post(
        "/api/files/upload",
        params={"library": "data"},
        files={"file": ("data-test.txt", b"content", "text/plain")},
    )
    assert response.status_code == 400


def test_delete_disallowed_library_fails():
    response = client.delete("/api/files", params={"library": "usb", "path": "firmware.bin"})
    assert response.status_code == 400


def test_serial_log_download_uses_actual_filename():
    upload = client.post(
        "/api/files/upload",
        params={"library": "personal"},
        files={"file": ("download-check.txt", b"content", "text/plain")},
    )
    assert upload.status_code == 200

    response = client.get(
        "/api/files/download",
        params={"library": "personal", "path": "download-check.txt"},
    )

    assert response.status_code == 200
    assert 'filename="download-check.txt"' in response.headers["content-disposition"]


def test_personal_listing_marks_files_deletable(tmp_path):
    settings = RuntimeSettings(content_root=tmp_path / "content", state_root=tmp_path / "state")
    service = StorageService(settings)
    (service.library_paths()["personal"] / "keep.txt").write_text("ok", encoding="utf-8")

    listing = service.list_library("personal")

    assert listing["items"][0]["deletable"] is True


def test_readme_route():
    response = client.get("/readme")
    assert response.status_code == 200
    assert "Fieldkit" in response.text


def test_settings_page_route():
    response = client.get("/settings")
    assert response.status_code == 200
    assert "Fieldkit Settings" in response.text
    assert "Connectivity" in response.text
    assert "Change Password" in response.text


def test_serial_profiles_route():
    response = client.get("/serial-settings")
    assert response.status_code == 200
    assert "Serial Profiles" in response.text
    assert "Console 1" in response.text


def test_serial_console_popup_route():
    response = client.get("/serial-console/0")
    assert response.status_code == 200
    assert "Fieldkit Console 1" in response.text
    assert "Reconnect" in response.text


def test_kit_docs_index_route():
    response = client.get("/kit-docs")
    assert response.status_code == 200
    assert "Fieldkit Reference Notes" in response.text


def test_kit_docs_topic_route():
    response = client.get("/kit-docs/netapp")
    assert response.status_code == 200
    assert "cluster show" in response.text


def test_update_settings():
    payload = {
        "hostname": "fieldkit",
        "ethernet": {
            "mode": "static",
            "address": "192.168.200.120/24",
            "gateway": "",
            "dns": [],
            "interface": "eth0",
        },
        "wifi": {
            "mode": "disabled",
            "ssid": "",
            "password": "",
            "country_code": "US",
        },
        "serial_ports": [
            {
                "label": "Console 1",
                "device_hint": "/dev/ttyUSB0",
                "baud_rate": 9600,
                "data_bits": 8,
                "parity": "none",
                "stop_bits": 1,
            },
            {
                "label": "Console 2",
                "device_hint": "/dev/ttyUSB1",
                "baud_rate": 115200,
                "data_bits": 8,
                "parity": "none",
                "stop_bits": 1,
            },
        ],
        "transfer_services": {
            "tftp_enabled": True,
            "ftp_enabled": False,
        },
    }
    response = client.put("/api/settings", json=payload)
    assert response.status_code == 200
    assert response.json()["serial_ports"][1]["baud_rate"] == 115200
    assert response.json()["transfer_services"]["tftp_enabled"] is True


def test_connectivity_apply_returns_commands():
    response = client.post("/api/connectivity/apply")
    assert response.status_code == 200
    payload = response.json()
    assert payload["dry_run"] is True
    assert any("hostnamectl set-hostname" in command for command in payload["commands"])


def test_connectivity_status_includes_platform_capabilities():
    response = client.get("/api/connectivity/status")
    assert response.status_code == 200
    payload = response.json()
    platform = payload["platform"]
    assert "wifi_supported" in platform
    assert "notes" in platform
    assert "active_connections" in payload


def test_serial_sessions_include_indexes():
    response = client.get("/api/serial/sessions")
    assert response.status_code == 200
    sessions = response.json()["sessions"]
    assert len(sessions) == 2
    assert sessions[0]["index"] == 0


def test_transfer_status_route():
    response = client.get("/api/transfers/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["http_base"] == "/fieldkit"
    assert payload["libraries"] == ["/fieldkit/data", "/fieldkit/personal", "/fieldkit/usb"]
    assert "tftp" in payload
    assert "ftp" in payload
    assert "scp" in payload
    assert "usb_gadget" in payload


def test_fieldkit_export_root_route():
    response = client.get("/fieldkit")
    assert response.status_code == 200
    assert "Fieldkit Exports" in response.text
    assert "/fieldkit/data" in response.text


def test_serial_profiles_auto_resolve_detected_devices(monkeypatch):
    service = SerialService()

    monkeypatch.setattr(service, "_detected_devices", lambda: ["/dev/ttyACM0", "/dev/ttyUSB3"])

    statuses = service.profile_status()

    assert statuses[0]["active_device"] == "/dev/ttyACM0"
    assert statuses[0]["present"] is True
    assert statuses[1]["active_device"] == "/dev/ttyUSB3"
    assert statuses[1]["present"] is True


def test_serial_profiles_prefer_matching_device_hint(monkeypatch):
    service = SerialService()

    monkeypatch.setattr(service, "_detected_devices", lambda: ["/dev/ttyUSB1", "/dev/ttyUSB9"])

    statuses = service.profile_status()

    assert statuses[1]["active_device"] == "/dev/ttyUSB1"


def test_serial_profiles_blank_device_hint_still_auto_resolves(monkeypatch):
    service = SerialService()
    settings = service._store.load()
    settings.serial_ports[0].device_hint = ""
    settings.serial_ports[1].device_hint = ""
    monkeypatch.setattr(service._store, "load", lambda: settings)
    monkeypatch.setattr(service, "_detected_devices", lambda: ["/dev/ttyUSB4", "/dev/ttyACM0"])

    statuses = service.profile_status()

    assert statuses[0]["active_device"] == "/dev/ttyUSB4"
    assert statuses[1]["active_device"] == "/dev/ttyACM0"


def test_serial_log_path_uses_timestamped_filename(tmp_path):
    service = SerialService()
    service._log_root = tmp_path

    class Profile:
        label = "Console 1"
        device_hint = "/dev/ttyUSB0"

    log_path = service._create_session_log_path(Profile())

    assert log_path.parent == tmp_path
    assert log_path.name.endswith("-console-1-ttyusb0.log")
    assert log_path.read_text(encoding="utf-8").startswith("[")
    assert "SYSTEM session opened for Console 1 on /dev/ttyUSB0" in log_path.read_text(encoding="utf-8")


def test_serial_log_entries_include_direction_and_timestamp(tmp_path):
    service = SerialService()
    log_path = Path(tmp_path) / "session.log"

    service._append_log_entry(log_path, "rx", "line 1\nline 2")
    service._append_log_entry(log_path, "tx", "show version\n")

    content = log_path.read_text(encoding="utf-8")
    assert "[20" in content
    assert "RX line 1" in content
    assert "RX line 2" in content
    assert "TX show version" in content


def test_library_listing_deduplicates_same_resolved_entry(tmp_path):
    settings = RuntimeSettings(content_root=tmp_path / "content", state_root=tmp_path / "state")
    service = StorageService(settings)
    usb_root = service.library_paths()["usb"]

    target = usb_root / "files"
    target.mkdir()
    alias = usb_root / "files-alias"
    alias.symlink_to(target, target_is_directory=True)

    listing = service.list_library("usb")

    names = [item["name"] for item in listing["items"]]
    assert "files" in names
    assert "files-alias" not in names


def test_library_listing_hides_dotfiles_and_macos_metadata(tmp_path):
    settings = RuntimeSettings(content_root=tmp_path / "content", state_root=tmp_path / "state")
    service = StorageService(settings)
    usb_root = service.library_paths()["usb"]

    (usb_root / "firmware.bin").write_text("ok", encoding="utf-8")
    (usb_root / "._firmware.bin").write_text("meta", encoding="utf-8")
    (usb_root / ".Spotlight-V100").mkdir()

    listing = service.list_library("usb")

    names = [item["name"] for item in listing["items"]]
    assert names == ["firmware.bin"]


def test_export_tree_contains_library_links(tmp_path):
    settings = RuntimeSettings(content_root=tmp_path / "content", state_root=tmp_path / "state")
    service = StorageService(settings)

    export_root = service.sync_export_tree()

    assert (export_root / "data").is_dir()
    assert (export_root / "personal").is_dir()
    assert (export_root / "usb").is_dir()
    assert not (export_root / "serial-logs").exists()


def test_export_tree_contains_mirrored_files_inside_real_library_dirs(tmp_path):
    settings = RuntimeSettings(content_root=tmp_path / "content", state_root=tmp_path / "state")
    service = StorageService(settings)
    (service.library_paths()["personal"] / "firmware.bin").write_text("payload", encoding="utf-8")

    export_root = service.sync_export_tree()

    assert (export_root / "personal").is_dir()
    assert (export_root / "personal" / "firmware.bin").is_file()
    assert (export_root / "personal" / "firmware.bin").read_text(encoding="utf-8") == "payload"


def test_resolve_export_path_uses_virtual_library_paths(tmp_path):
    settings = RuntimeSettings(content_root=tmp_path / "content", state_root=tmp_path / "state")
    service = StorageService(settings)
    target = service.library_paths()["personal"] / "image.bin"
    target.write_text("payload", encoding="utf-8")

    resolved = service.resolve_export_path("personal/image.bin")

    assert resolved == target.resolve()


def test_fieldkit_export_route_serves_file_from_virtual_library_path(tmp_path, monkeypatch):
    from app import main as app_main

    settings = RuntimeSettings(content_root=tmp_path / "content", state_root=tmp_path / "state")
    service = StorageService(settings)
    target = service.library_paths()["personal"] / "image.bin"
    target.write_text("payload", encoding="utf-8")
    monkeypatch.setattr(app_main, "storage_service", service)

    response = TestClient(app_main.app).get("/fieldkit/personal/image.bin")

    assert response.status_code == 200
    assert response.content == b"payload"


def test_transfer_status_does_not_sync_export_tree(monkeypatch):
    service = TransferService()
    monkeypatch.setattr(service._storage, "sync_export_tree", lambda: (_ for _ in ()).throw(AssertionError("should not sync")))

    status = service.get_status()

    assert status["root"].endswith("fieldkit")


def test_transfer_service_refuses_to_disable_ssh_with_active_sessions(monkeypatch):
    service = TransferService()
    settings = service._store.load()
    settings.transfer_services.ftp_enabled = False
    settings.transfer_services.tftp_enabled = False
    monkeypatch.setattr(service._store, "load", lambda: settings)
    monkeypatch.setattr(service._runtime, "dry_run_transfer_changes", False)
    monkeypatch.setattr(service._storage, "sync_export_tree", lambda: Path("/tmp/fieldkit"))
    monkeypatch.setattr(
        service,
        "_apply_unit",
        lambda unit, enabled: type("Result", (), {"ok": True, "stderr": "", "stdout": "", "returncode": 0})()
        if unit == "tftpd-hpa"
        else type("Result", (), {"ok": True, "stderr": "", "stdout": "", "returncode": 0})(),
    )

    result = service.apply_settings()

    assert result.applied is True
    assert any("vsftpd disabled." in note for note in result.notes)


def test_usb_gadget_status_reports_unsupported_when_no_udc(monkeypatch):
    service = TransferService()
    monkeypatch.setattr(service, "_read_text", lambda path: "Raspberry Pi 3 Model B Rev 1.2\x00")
    monkeypatch.setattr(service, "_list_dir_names", lambda path: [])

    status = service._usb_gadget_status()

    assert status["supported"] is False
    assert "Raspberry Pi 3 Model B" in status["model"]


def test_usb_gadget_status_reports_supported_when_udc_present(monkeypatch):
    service = TransferService()
    monkeypatch.setattr(service, "_read_text", lambda path: "Raspberry Pi 4 Model B Rev 1.5\x00")
    monkeypatch.setattr(service, "_list_dir_names", lambda path: ["20980000.usb"])

    status = service._usb_gadget_status()

    assert status["supported"] is True
    assert status["controllers"] == ["20980000.usb"]
