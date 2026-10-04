from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app, serial_console_window
from app.api.routes.connectivity import network_service
from app.core.config import RuntimeSettings
from app.core.models import AppSettingsPayload
from app.services.serial import SerialService
from app.services.storage import StorageService
from app.services.transfers import TransferService


client = TestClient(app)


TEST_FILE_NAMES = {"delete-me.txt", "usb-test.txt", "duplicate.txt", "download-check.txt", "usb-delete-me.txt"}


def test_default_settings_enable_fieldkit_access_point():
    wifi = AppSettingsPayload().wifi
    assert wifi.mode == "ap"
    assert wifi.ssid == "fieldkit"
    assert wifi.password == "fieldkit"


def test_default_settings_use_dhcp_ethernet():
    assert AppSettingsPayload().ethernet.mode == "dhcp"


def test_static_ethernet_apply_sets_address_and_mode_together(monkeypatch):
    monkeypatch.setattr(network_service, "_resolve_ethernet_connection", lambda settings: "netplan-eth0")
    payload = AppSettingsPayload(
        ethernet={"mode": "static", "address": "192.168.200.120/24", "interface": "eth0"}
    )
    commands = network_service._ethernet_commands(payload)

    assert len(commands) == 1
    command = commands[0]
    assert command[command.index("ipv4.method") + 1] == "manual"
    assert command[command.index("ipv4.addresses") + 1] == "192.168.200.120/24"


@pytest.fixture(autouse=True)
def clean_runtime_state():
    runtime = RuntimeSettings()
    settings_path = runtime.state_root / runtime.settings_file
    if settings_path.exists():
        settings_path.unlink()
    for library in (runtime.personal_dir_name, runtime.usb_dir_name):
        for name in TEST_FILE_NAMES:
            path = runtime.content_root / library / name
            if path.exists():
                path.unlink()
    yield
    for library in (runtime.personal_dir_name, runtime.usb_dir_name):
        for name in TEST_FILE_NAMES:
            path = runtime.content_root / library / name
            if path.exists():
                path.unlink()



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
    response = client.delete("/api/files", params={"library": "data", "path": "firmware.bin"})
    assert response.status_code == 400


def test_delete_usb_file():
    upload = client.post(
        "/api/files/upload",
        params={"library": "usb"},
        files={"file": ("usb-delete-me.txt", b"content", "text/plain")},
    )
    assert upload.status_code == 200
    response = client.delete("/api/files", params={"library": "usb", "path": "usb-delete-me.txt"})
    assert response.status_code == 200
    assert response.json()["deleted"] is True


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


def test_copy_to_usb_route(tmp_path, monkeypatch):
    from app.api.routes import files as files_module
    from app.services.storage import StorageService
    from app.services.usb_copy_job import UsbCopyJob

    settings = RuntimeSettings(content_root=tmp_path / "content", state_root=tmp_path / "state")
    storage = StorageService(settings)
    usb = tmp_path / "usb"
    usb.mkdir()
    monkeypatch.setattr(storage, "_detect_usb_mount", lambda: usb)
    source = storage.library_paths()["data"] / "brocade" / "route-fw.bin"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"route")
    job = UsbCopyJob(storage)
    monkeypatch.setattr(files_module, "storage_service", storage)
    monkeypatch.setattr(files_module, "usb_copy_job", job)
    try:
        response = client.post(
            "/api/files/copy-to-usb", params={"library": "data", "path": "brocade/route-fw.bin"}
        )
        assert response.status_code == 202
        job.stop()
        state = job.status()
        assert state["running"] is False
        assert state["last"]["outcome"] == "success"
        assert (usb / "brocade" / "route-fw.bin").read_bytes() == b"route"
    finally:
        job.stop()


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


def test_dashboard_links_to_tools():
    response = client.get("/")
    assert response.status_code == 200
    assert 'href="/tools"' in response.text


def test_tools_page_includes_subnet_calculator():
    response = client.get("/tools")
    assert response.status_code == 200
    assert "Subnet Calculator" in response.text
    assert 'id="subnet-form"' in response.text
    assert "/static/app.js?v=ui-0.2.2-20261003e" in response.text


def test_subnet_calculator_has_supported_language_strings():
    import re

    app_js = Path("app/static/app.js").read_text(encoding="utf-8")
    keys = [
        "nav_tools",
        "subnet_calculator",
        "subnet_note",
        "ip_address",
        "cidr_prefix",
        "calculate",
        "subnet_invalid_ip",
        "subnet_invalid_prefix",
        "subnet_network",
        "subnet_netmask",
        "subnet_wildcard",
        "subnet_broadcast",
        "subnet_host_range",
        "subnet_hosts",
        "subnet_single_host",
        "subnet_point_to_point",
    ]
    for language in ("es", "de", "nl", "fr"):
        match = re.search(rf"TRANSLATIONS\.{language} = \{{(.*?)\n\}};", app_js, re.S)
        assert match, f"missing {language} translation block"
        block = match.group(1)
        for key in keys:
            assert f"{key}:" in block, f"{language} is missing {key}"


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


def test_serial_console_does_not_block_spacebar():
    import asyncio
    response = asyncio.run(serial_console_window(0))
    body = response.body.decode()
    assert 'event.key === " "' not in body
    assert 'event.key === "PageUp"' in body
    assert "terminalEvent" in body


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
            "mode": "ap",
            "ssid": "fieldkit",
            "password": "fieldkitpass",
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
    # Secrets are never returned to clients.
    assert response.json()["wifi"]["password"] == ""
    assert client.get("/api/settings").json()["wifi"]["password"] == ""
    assert response.json()["transfer_services"]["tftp_enabled"] is True


def test_connectivity_apply_returns_commands(monkeypatch):
    monkeypatch.setattr(network_service._settings, "dry_run_system_changes", True)
    response = client.post("/api/connectivity/apply")
    assert response.status_code == 200
    payload = response.json()
    assert payload["dry_run"] is True
    assert any("set_appliance_hostname.sh" in command for command in payload["commands"])


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


def test_update_status_route_returns_dict():
    response = client.get("/api/system/update/status")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_update_rollback_reports_not_installed(monkeypatch, tmp_path):
    from app.api.routes import updates as updates_module

    monkeypatch.setattr(updates_module, "ROLLBACK_SCRIPT", tmp_path / "missing.sh")
    response = client.post("/api/system/update/rollback")
    assert response.status_code == 501


def test_update_rollback_runs_in_its_own_unit(monkeypatch, tmp_path):
    from app.api.routes import updates as updates_module

    script = tmp_path / "rollback_appliance.sh"
    script.write_text("#!/bin/bash\n", encoding="utf-8")
    monkeypatch.setattr(updates_module, "ROLLBACK_SCRIPT", script)
    calls = []
    monkeypatch.setattr(updates_module.subprocess, "run", lambda *a, **k: calls.append(a[0]))
    monkeypatch.setattr(updates_module.subprocess, "Popen", lambda *a, **k: calls.append(a[0]))

    response = client.post("/api/system/update/rollback")
    assert response.status_code == 202
    # The rollback must run outside fieldkit-web's cgroup, via its own unit, or
    # stopping the web service would kill the rollback mid-flight.
    assert ["sudo", "/usr/bin/systemctl", "start", "--no-block", "fieldkit-rollback.service"] in calls


def test_first_boot_defaults_to_ap_and_seeds_settings():
    startup = Path("scripts/apply_startup_network_mode.sh").read_text(encoding="utf-8")
    sysprep = Path("scripts/golden-chroot-install.sh").read_text(encoding="utf-8")
    # No settings file -> bring up the AP instead of skipping networking.
    assert "defaulting to AP mode" in startup
    # The image seeds a default settings.json in sysprep for first boot.
    assert "AppSettingsPayload" in sysprep


def test_golden_image_offline_unit_state_and_console():
    chroot = Path("scripts/golden-chroot-install.sh").read_text(encoding="utf-8")
    web = Path("deploy/systemd/fieldkit-web.service").read_text(encoding="utf-8")
    assert "systemctl --root=/" in chroot          # real offline enable/mask
    assert "enforce_image_state" in chroot
    assert "fieldkit-startup-network.timer" in chroot
    assert "After=network.target" in web           # web server is not gated on DHCP
    assert "network-online.target" not in web
    assert Path("deploy/systemd/fieldkit-startup-network.timer").is_file()
    assert Path("deploy/systemd/fieldkit-growroot.timer").is_file()


def test_update_bundle_ships_version_and_health_check():
    build = Path("scripts/build_update_bundle.sh").read_text(encoding="utf-8")
    updater = Path("scripts/update_appliance.sh").read_text(encoding="utf-8")
    unit = Path("deploy/systemd/fieldkit-post-update.service").read_text(encoding="utf-8")
    assert "pyproject.toml" in build  # version source travels with the bundle
    assert "fieldkit-post-update.service" in updater  # persistent health-check unit
    assert "post_update_check.sh" in unit  # restart is gated by a health check


def test_transfer_status_route():
    response = client.get("/api/transfers/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["http_base"] == "/fieldkit"
    assert payload["libraries"] == ["/fieldkit/data", "/fieldkit/personal"]
    assert "tftp" in payload
    assert "ftp" in payload
    assert "scp" in payload
    assert "usb_gadget" in payload


def test_fieldkit_export_root_route():
    response = client.get("/fieldkit")
    assert response.status_code == 200
    assert "Fieldkit Exports" in response.text
    assert '"path": "data"' in response.text


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
    settings = service._store.load()
    settings.serial_ports[1].device_hint = "/dev/ttyUSB1"
    monkeypatch.setattr(service._store, "load", lambda: settings)
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


def test_serial_detected_adapters_include_stable_by_id(monkeypatch, tmp_path):
    service = SerialService()
    tty0 = tmp_path / "ttyUSB0"
    tty0.write_text("")
    by_id = tmp_path / "by-id"
    by_id.mkdir()
    link = by_id / "usb-FTDI_FT232R_USB_UART_A9O86941-if00-port0"
    link.symlink_to(tty0)
    monkeypatch.setattr(service, "_detected_devices", lambda: [str(tty0)])
    monkeypatch.setattr(service, "_serial_by_id_root", by_id)
    monkeypatch.setattr(service, "_serial_by_path_root", tmp_path / "by-path")

    adapters = service.list_adapters()

    assert len(adapters) == 1
    assert adapters[0]["by_id"] == str(link)
    assert adapters[0]["tty"] == str(tty0)
    assert "ttyUSB0" in adapters[0]["label"]


def test_serial_profile_by_id_pin_survives_tty_renumber(monkeypatch, tmp_path):
    service = SerialService()
    tty0 = tmp_path / "ttyUSB0"
    tty0.write_text("")
    tty1 = tmp_path / "ttyUSB1"
    tty1.write_text("")
    by_id = tmp_path / "by-id"
    by_id.mkdir()
    link_a = by_id / "usb-FTDI_FT232R_USB_UART_A9O86941-if00-port0"
    link_b = by_id / "usb-FTDI_FT232R_USB_UART_A95HRISR-if00-port0"
    link_a.symlink_to(tty1)
    link_b.symlink_to(tty0)
    monkeypatch.setattr(service, "_detected_devices", lambda: [str(tty0), str(tty1)])
    monkeypatch.setattr(service, "_serial_by_id_root", by_id)
    monkeypatch.setattr(service, "_serial_by_path_root", tmp_path / "by-path")

    settings = service._store.load()
    settings.serial_ports[0].device_hint = str(link_a)
    settings.serial_ports[1].device_hint = str(link_b)
    monkeypatch.setattr(service._store, "load", lambda: settings)

    statuses = service.profile_status()

    assert statuses[0]["active_device"] == str(link_a)
    assert statuses[0]["tty_device"] == str(tty1)
    assert statuses[0]["bound"] is True
    assert statuses[1]["active_device"] == str(link_b)
    assert statuses[1]["tty_device"] == str(tty0)


def test_serial_pinned_absent_adapter_does_not_steal_another(monkeypatch, tmp_path):
    service = SerialService()
    tty0 = tmp_path / "ttyUSB0"
    tty0.write_text("")
    by_id = tmp_path / "by-id"
    by_id.mkdir()
    (by_id / "usb-FTDI_FT232R_USB_UART_A95HRISR-if00-port0").symlink_to(tty0)
    monkeypatch.setattr(service, "_detected_devices", lambda: [str(tty0)])
    monkeypatch.setattr(service, "_serial_by_id_root", by_id)
    monkeypatch.setattr(service, "_serial_by_path_root", tmp_path / "by-path")

    settings = service._store.load()
    settings.serial_ports[0].device_hint = "/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A9O86941-if00-port0"
    monkeypatch.setattr(service._store, "load", lambda: settings)

    statuses = service.profile_status()

    assert statuses[0]["present"] is False
    assert statuses[0]["active_device"] is None
    assert statuses[0]["bound"] is False
    assert statuses[1]["present"] is True
    assert statuses[1]["tty_device"] == str(tty0)


def test_serial_opens_by_path_when_no_unique_serial(monkeypatch, tmp_path):
    service = SerialService()
    tty0 = tmp_path / "ttyUSB0"
    tty0.write_text("")
    by_path = tmp_path / "by-path"
    by_path.mkdir()
    link = by_path / "platform-xhci-hcd.0-usb-0:2:1.0-port0"
    link.symlink_to(tty0)
    monkeypatch.setattr(service, "_detected_devices", lambda: [str(tty0)])
    monkeypatch.setattr(service, "_serial_by_id_root", tmp_path / "by-id")
    monkeypatch.setattr(service, "_serial_by_path_root", by_path)

    statuses = service.profile_status()

    assert statuses[0]["active_device"] == str(link)
    assert statuses[0]["tty_device"] == str(tty0)


def test_serial_adapters_route():
    response = client.get("/api/serial/adapters")
    assert response.status_code == 200
    assert "adapters" in response.json()


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

    with log_path.open("a", encoding="utf-8") as handle:
        service._append_log_entry(handle, "rx", "line 1\nline 2")
        service._append_log_entry(handle, "tx", "show version\n")

    content = log_path.read_text(encoding="utf-8")
    assert "[20" in content
    assert "RX line 1" in content
    assert "RX line 2" in content
    assert "TX show version" in content


def test_serial_writer_preserves_common_console_input():
    service = SerialService()

    class FakeSerial:
        def __init__(self):
            self.writes = []

        def write(self, payload):
            self.writes.append(payload)

    fake_serial = FakeSerial()
    for message in [
        "show version\n",
        "configure terminal\n",
        "interface Gi0/1\n",
        "description Uplink Port\n",
        "ping 192.168.1.1\n",
        "\t",
        "\x1b[A",
        "\x03",
    ]:
        service._write_serial_payload(fake_serial, message)

    assert fake_serial.writes == [
        b"show version\n",
        b"configure terminal\n",
        b"interface Gi0/1\n",
        b"description Uplink Port\n",
        b"ping 192.168.1.1\n",
        b"\t",
        b"\x1b[A",
        b"\x03",
    ]


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
    assert not (export_root / "usb").exists()
    assert not (export_root / "serial-logs").exists()


def test_export_tree_contains_mirrored_files_inside_real_library_dirs(tmp_path):
    settings = RuntimeSettings(content_root=tmp_path / "content", state_root=tmp_path / "state")
    service = StorageService(settings)
    (service.library_paths()["personal"] / "firmware.bin").write_text("payload", encoding="utf-8")

    export_root = service.sync_export_tree()

    assert (export_root / "personal").is_dir()
    assert (export_root / "personal" / "firmware.bin").is_file()
    assert (export_root / "personal" / "firmware.bin").read_text(encoding="utf-8") == "payload"


def test_export_tree_hardlinks_same_filesystem(tmp_path):
    import os

    settings = RuntimeSettings(content_root=tmp_path / "content", state_root=tmp_path / "state")
    service = StorageService(settings)
    source = service.library_paths()["personal"] / "firmware.bin"
    source.write_text("payload", encoding="utf-8")

    service.sync_export_tree()
    export = service.export_root() / "personal" / "firmware.bin"
    assert os.stat(source).st_ino == os.stat(export).st_ino

    # In-place edit is visible through the shared inode; a rename-replace is relinked.
    source.write_text("in place", encoding="utf-8")
    service.sync_export_tree()
    assert export.read_text(encoding="utf-8") == "in place"

    replacement = source.with_suffix(".tmp")
    replacement.write_text("replaced", encoding="utf-8")
    os.replace(replacement, source)
    service.sync_export_tree()
    assert os.stat(source).st_ino == os.stat(export).st_ino
    assert export.read_text(encoding="utf-8") == "replaced"


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


def test_transfer_apply_skips_when_nothing_changed(monkeypatch):
    service = TransferService()
    settings = service._store.load()
    settings.transfer_services.http_export_enabled = False
    settings.transfer_services.ftp_enabled = False
    settings.transfer_services.tftp_enabled = False
    monkeypatch.setattr(service._store, "load", lambda: settings)
    monkeypatch.setattr(service._runtime, "dry_run_transfer_changes", False)
    monkeypatch.setattr(service._storage, "sync_export_tree", lambda: Path("/tmp/fieldkit"))

    def fake_run(command, env=None):
        unit = command[-1]
        if command[-2] == "is-active":
            return type("Result", (), {"ok": True, "stderr": "", "stdout": "inactive", "returncode": 0})()
        if command[-2] == "is-enabled":
            return type("Result", (), {"ok": True, "stderr": "", "stdout": "disabled" if unit in {"tftpd-hpa", "vsftpd"} else "enabled", "returncode": 0})()
        return type("Result", (), {"ok": True, "stderr": "", "stdout": "", "returncode": 0})()

    monkeypatch.setattr(service._runner, "run", fake_run)
    monkeypatch.setattr(
        service,
        "_apply_http_export",
        lambda enabled: type("Result", (), {"ok": True, "stderr": "", "stdout": "", "returncode": 0})(),
    )

    result = service.apply_settings()

    assert result.applied is True
    assert any("No transfer service state changes detected" in note for note in result.notes)
    assert "install_transfer_services.sh" not in "\n".join(result.commands)


def test_transfer_apply_applies_http_export_change(monkeypatch):
    service = TransferService()
    settings = service._store.load()
    settings.transfer_services.http_export_enabled = True
    settings.transfer_services.ftp_enabled = False
    settings.transfer_services.tftp_enabled = False
    monkeypatch.setattr(service._store, "load", lambda: settings)
    monkeypatch.setattr(service._runtime, "dry_run_transfer_changes", False)
    monkeypatch.setattr(service._storage, "sync_export_tree", lambda: Path("/tmp/fieldkit"))

    def fake_run(command, env=None):
        unit = command[-1]
        if command[-2] == "is-active":
            return type("Result", (), {"ok": True, "stderr": "", "stdout": "inactive", "returncode": 0})()
        if command[-2] == "is-enabled":
            return type("Result", (), {"ok": True, "stderr": "", "stdout": "disabled" if unit in {"tftpd-hpa", "vsftpd"} else "enabled", "returncode": 0})()
        return type("Result", (), {"ok": True, "stderr": "", "stdout": "", "returncode": 0})()

    monkeypatch.setattr(service._runner, "run", fake_run)

    apply_http_calls = []
    def fake_apply_http(enabled):
        apply_http_calls.append(enabled)
        return type("Result", (), {"ok": True, "stderr": "", "stdout": "", "returncode": 0})()

    monkeypatch.setattr(service, "_apply_http_export", fake_apply_http)

    result = service.apply_settings()

    assert result.applied is True
    assert apply_http_calls == [True]
    assert any("http export enabled" in note for note in result.notes)


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


def test_update_latest_reports_up_to_date_when_server_unavailable(monkeypatch):
    from app.api.routes import updates
    from app.core.config import RuntimeSettings
    monkeypatch.setattr(updates, "get_settings", lambda: RuntimeSettings(content_root="/tmp/fk", state_root="/tmp/fk-state"))
    monkeypatch.setattr(updates, "VERSION_PATH", __import__("pathlib").Path("/tmp/fk/pyproject.toml"))

    class FailingClient:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, path):
            raise __import__("httpx").ConnectError("down")

    monkeypatch.setattr(updates, "_client", lambda: (FailingClient(), None))
    result = updates.update_latest()
    assert result["available"] is False
    assert "Could not reach" in result["error"]


def test_update_client_uses_origin_bound_effective_credentials(monkeypatch, tmp_path):
    from app.api.routes import updates
    from app.services import settings_store
    from app.services import server_sync
    from app.services.server_sync import DEVICE_TOKEN_ENV

    runtime = RuntimeSettings(content_root=tmp_path, state_root=tmp_path, server_base_url="https://kit.example")
    monkeypatch.setattr(updates, "get_settings", lambda: runtime)
    monkeypatch.setattr(server_sync, "get_settings", lambda: runtime)
    monkeypatch.setattr(settings_store, "get_settings", lambda: runtime)
    monkeypatch.setenv(DEVICE_TOKEN_ENV, "runtime-token")
    client, _ = updates._client()
    try:
        assert str(client.base_url) == "https://kit.example/"
        assert client.headers["authorization"] == "Bearer runtime-token"
    finally:
        client.close()


def test_settings_route_keeps_token_for_same_origin_only(monkeypatch, tmp_path):
    from app.api.routes import settings as settings_route
    from app.services.settings_store import SettingsStore

    store = SettingsStore()
    store.path = tmp_path / "settings.json"
    existing = AppSettingsPayload()
    existing.server_sync.base_url = "https://same.example"
    existing.server_sync.device_token = "saved-token"
    store.save(existing)
    monkeypatch.setattr(settings_route, "store", store)
    same = existing.model_dump()
    same["server_sync"]["base_url"] = "https://SAME.example/path"
    same["server_sync"]["device_token"] = ""
    assert client.put("/api/settings", json=same).status_code == 200
    assert store.load().server_sync.device_token == "saved-token"
    changed = existing.model_dump()
    changed["server_sync"]["base_url"] = "https://other.example"
    changed["server_sync"]["device_token"] = ""
    assert client.put("/api/settings", json=changed).status_code == 200
    assert store.load().server_sync.device_token == ""


def test_update_latest_detects_newer_version(monkeypatch, tmp_path):
    from app.api.routes import updates
    from app.core.config import RuntimeSettings
    from app.services import settings_store as ss
    version_file = tmp_path / "pyproject.toml"
    version_file.write_text('version = "0.1.6"\n')
    monkeypatch.setattr(updates, "get_settings", lambda: RuntimeSettings(content_root=tmp_path, state_root=tmp_path))
    monkeypatch.setattr(ss, "get_settings", lambda: RuntimeSettings(content_root=tmp_path, state_root=tmp_path))
    monkeypatch.setattr(updates, "VERSION_PATH", version_file)

    class StubClient:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, path):
            response = __import__("httpx").Response(200, json={
                "available": True, "version": "0.1.7",
                "url": "https://cdn.example/bundle.tgz", "sha256": "a" * 64,
            })
            response.raise_for_status = lambda: None
            return response

    monkeypatch.setattr(updates, "_client", lambda: (StubClient(), None))
    result = updates.update_latest()
    assert result["available"] is True
    assert result["update_available"] is True
    assert result["latest_version"] == "0.1.7"


def test_update_apply_requires_valid_payload_and_script(monkeypatch, tmp_path):
    from app.api.routes import updates
    from fastapi import HTTPException

    monkeypatch.setattr(updates, "UPDATE_SCRIPT", tmp_path / "missing.sh")
    monkeypatch.setattr(updates, "update_latest", lambda: {"available": False})
    try:
        updates.update_apply({})
        assert False, "expected no-update failure"
    except HTTPException as exc:
        assert exc.status_code == 409

    published = {"available": True, "latest_version": "0.1.7",
                 "url": "https://cdn.example/b.tgz", "sha256": "b" * 64}
    monkeypatch.setattr(updates, "update_latest", lambda: published)
    try:
        updates.update_apply({"version": "0.1.7"})
        assert False, "expected missing-script failure"
    except HTTPException as exc:
        assert exc.status_code == 501

    try:
        updates.update_apply({"version": "0.0.1"})
        assert False, "expected version-mismatch failure"
    except HTTPException as exc:
        assert exc.status_code == 409


def test_update_apply_rejects_bad_server_metadata(monkeypatch, tmp_path):
    from app.api.routes import updates
    from fastapi import HTTPException

    script = tmp_path / "update_appliance.sh"
    script.write_text("#!/bin/bash\nexit 0\n")
    monkeypatch.setattr(updates, "UPDATE_SCRIPT", script)

    monkeypatch.setattr(updates, "update_latest",
                        lambda: {"available": True, "latest_version": "0.1.7",
                                 "url": "http://cdn.example/b.tgz", "sha256": "b" * 64})
    try:
        updates.update_apply({"version": "0.1.7"})
        assert False, "expected non-https rejection"
    except HTTPException as exc:
        assert exc.status_code == 400

    monkeypatch.setattr(updates, "update_latest",
                        lambda: {"available": True, "latest_version": "0.1.7",
                                 "url": "https://cdn.example/b.tgz", "sha256": "zz"})
    try:
        updates.update_apply({"version": "0.1.7"})
        assert False, "expected malformed-sha rejection"
    except HTTPException as exc:
        assert exc.status_code == 400


def test_update_apply_launches_script(monkeypatch, tmp_path):
    from app.api.routes import updates
    script = tmp_path / "update_appliance.sh"
    script.write_text("#!/bin/bash\nexit 0\n")
    calls = []
    monkeypatch.setattr(updates, "UPDATE_SCRIPT", script)
    monkeypatch.setattr(updates, "update_latest",
                        lambda: {"available": True, "latest_version": "0.1.7",
                                 "url": "https://cdn.example/b.tgz", "sha256": "c" * 64})
    monkeypatch.setattr(updates.subprocess, "Popen", lambda *args, **kwargs: calls.append((args, kwargs)))
    # Caller-supplied url/sha must be ignored in favour of the published latest.
    result = updates.update_apply({"version": "0.1.7", "url": "https://evil.example/x.tgz", "sha256": "e" * 64})
    assert result["started"] is True
    assert len(calls) == 1
    argv = calls[0][0][0]
    assert argv[:3] == ["sudo", "/bin/bash", str(script)]
    assert argv[3:] == ["0.1.7", "https://cdn.example/b.tgz", "c" * 64]


def test_json_for_script_escapes_script_terminators():
    from app.main import _json_for_script

    encoded = _json_for_script({"name": "</script><script>alert(1)</script>"})
    assert "</script>" not in encoded
    assert "<" not in encoded and ">" not in encoded


def test_export_hidden_paths_are_rejected():
    response = client.get("/fieldkit/personal/.hidden-secret")
    assert response.status_code == 400


def test_settings_validators_reject_injection():
    import pytest
    from pydantic import ValidationError
    from app.core.models import AppSettingsPayload, WifiConfig

    with pytest.raises(ValidationError):
        AppSettingsPayload(hostname="evil\n1.2.3.4 host")
    with pytest.raises(ValidationError):
        WifiConfig(ssid="evil\nssid=1")
    with pytest.raises(ValidationError):
        WifiConfig(password="short\nwpa=1")
    with pytest.raises(ValidationError):
        WifiConfig(country_code="USA")


def test_upload_refuses_symlinked_target_and_leaves_no_temp(tmp_path):
    import io

    settings = RuntimeSettings(content_root=tmp_path / "content", state_root=tmp_path / "state")
    service = StorageService(settings)
    lib = service.library_paths()["personal"]
    lib.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside.txt"
    outside.write_text("original", encoding="utf-8")
    (lib / "evil.txt").symlink_to(outside)

    with pytest.raises(FileExistsError):
        service.save_upload("personal", "evil.txt", io.BytesIO(b"attacker"))

    assert outside.read_text(encoding="utf-8") == "original"
    assert list(lib.glob(".*upload*")) == []


def test_upload_publishes_atomically_and_cleans_temp(tmp_path):
    import io

    settings = RuntimeSettings(content_root=tmp_path / "content", state_root=tmp_path / "state")
    service = StorageService(settings)
    target = service.save_upload("personal", "firmware.bin", io.BytesIO(b"payload"))

    assert target.read_text(encoding="utf-8") == "payload"
    assert list(target.parent.glob(".*upload*")) == []


def test_transfer_apply_reconciles_enabled_services(monkeypatch):
    service = TransferService()
    settings = service._store.load()
    settings.transfer_services.http_export_enabled = True
    settings.transfer_services.ftp_enabled = True
    settings.transfer_services.tftp_enabled = False
    monkeypatch.setattr(service._store, "load", lambda: settings)
    monkeypatch.setattr(service._runtime, "dry_run_transfer_changes", False)
    monkeypatch.setattr(service._storage, "sync_export_tree", lambda: Path("/tmp/fieldkit"))
    monkeypatch.setattr(service, "_http_export_status", lambda enabled: {"active": True, "enabled": True})

    recorded: list[list[str]] = []

    def fake_run(command, env=None):
        recorded.append(list(command))
        if command[-2] == "is-active":
            return type("Result", (), {"ok": True, "stderr": "", "stdout": "inactive", "returncode": 0})()
        if command[-2] == "is-enabled":
            return type("Result", (), {"ok": True, "stderr": "", "stdout": "disabled", "returncode": 0})()
        return type("Result", (), {"ok": True, "stderr": "", "stdout": "", "returncode": 0})()

    monkeypatch.setattr(service._runner, "run", fake_run)
    monkeypatch.setattr(
        service, "_apply_http_export",
        lambda enabled: type("Result", (), {"ok": True, "stderr": "", "stdout": "", "returncode": 0})(),
    )

    result = service.apply_settings()

    assert result.applied is True
    # FTP was configured on and inactive (a change); the installer disables both,
    # so vsftpd must be re-enabled and tftpd-hpa left disabled.
    assert ["sudo", "-n", "systemctl", "enable", "--now", "vsftpd"] in recorded
    assert ["sudo", "-n", "systemctl", "disable", "--now", "tftpd-hpa"] in recorded


def test_network_preview_activates_ethernet_in_ap_mode(monkeypatch):
    monkeypatch.setattr(network_service, "_resolve_ethernet_connection", lambda settings: "fieldkit-wired")
    settings = AppSettingsPayload()
    settings.wifi.mode = "ap"

    commands = network_service._build_apply_commands(settings)

    assert any("nmcli connection up fieldkit-wired" in command for command in commands)
