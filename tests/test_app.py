from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_system_status():
    response = client.get("/api/system/status")
    assert response.status_code == 200
    assert response.json()["hostname"] == "fieldkit"


def test_file_libraries():
    response = client.get("/api/files/libraries")
    assert response.status_code == 200
    names = {entry["name"] for entry in response.json()["libraries"]}
    assert {"data", "personal", "usb"} <= names


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
    }
    response = client.put("/api/settings", json=payload)
    assert response.status_code == 200
    assert response.json()["serial_ports"][1]["baud_rate"] == 115200


def test_connectivity_apply_returns_commands():
    response = client.post("/api/connectivity/apply")
    assert response.status_code == 200
    payload = response.json()
    assert payload["dry_run"] is True
    assert any("hostnamectl set-hostname" in command for command in payload["commands"])


def test_connectivity_status_includes_platform_capabilities():
    response = client.get("/api/connectivity/status")
    assert response.status_code == 200
    platform = response.json()["platform"]
    assert "wifi_supported" in platform
    assert "notes" in platform


def test_serial_sessions_include_indexes():
    response = client.get("/api/serial/sessions")
    assert response.status_code == 200
    sessions = response.json()["sessions"]
    assert len(sessions) == 2
    assert sessions[0]["index"] == 0
