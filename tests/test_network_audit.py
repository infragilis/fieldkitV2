from app.core.models import AppSettingsPayload
from app.services.command_runner import CommandResult
from app.services.network import NetworkService
from app.api.routes.connectivity import network_service


def test_wifi_preview_and_execution_omit_psk(monkeypatch):
    service = NetworkService()
    settings = AppSettingsPayload()
    settings.wifi.password = "distinctive-psk-123"
    command = service._wifi_apply_command(settings)
    assert "distinctive-psk-123" not in command
    calls = []
    monkeypatch.setattr(service._runner, "run_with_input", lambda cmd, data: calls.append((cmd, data)) or CommandResult(True, cmd))
    service._apply_wifi_mode(settings)
    assert calls[0][0] == command
    assert calls[0][1] == "distinctive-psk-123\n"


def test_connectivity_apply_response_omits_psk(monkeypatch):
    settings = AppSettingsPayload()
    settings.wifi.password = "distinctive-response-psk-456"
    monkeypatch.setattr(network_service._store, "load", lambda: settings)
    monkeypatch.setattr(network_service._platform, "detect", lambda: {"wifi_supported": True})
    monkeypatch.setattr(network_service._settings, "dry_run_system_changes", True)

    payload = network_service.apply_settings().model_dump_json()
    assert "distinctive-response-psk-456" not in payload


def test_nmcli_escaped_colons_and_bad_rows(monkeypatch):
    service = NetworkService()
    monkeypatch.setattr(service._platform, "detect", lambda: {"wifi_supported": True})
    monkeypatch.setattr(service._runner, "available", lambda _: True)
    monkeypatch.setattr(service._runner, "run", lambda _: CommandResult(
        True, [], "Cafe\\:Net:75:WPA2\nmalformed\nBad:signal:nope\n", ""
    ))
    assert service.scan_wifi_networks() == [{"ssid": "Cafe:Net", "signal": 75, "secure": True}]


def test_active_nmcli_escaped_colons(monkeypatch):
    service = NetworkService()
    monkeypatch.setattr(service._runner, "available", lambda _: True)
    monkeypatch.setattr(service._runner, "run", lambda _: CommandResult(
        True, [], "Office\\:VPN:wlan0:vpn:activated\n", ""
    ))
    assert service._active_connections()[0]["name"] == "Office:VPN"
