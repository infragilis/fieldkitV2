from app.core.config import get_settings
from app.core.models import AppSettingsPayload, ApplyResult
from app.services.command_runner import CommandRunner
from app.services.platform import PlatformService
from app.services.settings_store import SettingsStore


class NetworkService:
    """Boundary for Pi network configuration and status."""

    def __init__(self) -> None:
        self._store = SettingsStore()
        self._runner = CommandRunner()
        self._settings = get_settings()
        self._platform = PlatformService()

    def get_status(self) -> dict:
        settings = self._store.load()
        interfaces = self._detect_interfaces()
        platform = self._platform.detect()
        active_connections = self._active_connections()
        return {
            "hostname": settings.hostname,
            "ethernet": settings.ethernet.model_dump(),
            "wifi": settings.wifi.model_dump(),
            "interfaces": interfaces,
            "active_connections": active_connections,
            "platform": platform,
            "applied": False,
            "dry_run": self._settings.dry_run_system_changes,
            "note": "Apply actions are prepared, but host network changes remain dry-run by default.",
        }

    def scan_wifi_networks(self) -> list[dict]:
        if not self._platform.detect()["wifi_supported"]:
            return []
        if self._runner.available("nmcli"):
            result = self._runner.run(["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "dev", "wifi", "list"])
            if result.ok:
                networks = []
                for line in result.stdout.splitlines():
                    parts = line.split(":")
                    if len(parts) < 3:
                        continue
                    ssid, signal, security = parts[0], parts[1], ":".join(parts[2:])
                    if not ssid:
                        continue
                    networks.append(
                        {"ssid": ssid, "signal": int(signal or "0"), "secure": bool(security.strip())}
                    )
                return networks
        return [
            {"ssid": "Fieldkit-AP", "signal": 100, "secure": True},
            {"ssid": "Example-WAN", "signal": 62, "secure": True},
        ]

    def apply_settings(self) -> ApplyResult:
        settings = self._store.load()
        notes = []
        platform = self._platform.detect()
        if settings.wifi.mode != "disabled" and not platform["wifi_supported"]:
            notes.append("Wi-Fi configuration skipped because the detected platform does not include onboard Wi-Fi.")
            settings.wifi.mode = "disabled"
        commands = self._build_apply_commands(settings)
        if self._settings.dry_run_system_changes:
            notes.append("Dry-run mode enabled. No system network changes were executed.")
            return ApplyResult(applied=False, dry_run=True, commands=commands, notes=notes)
        execution = self._execute_apply(settings)
        notes.extend(execution["notes"])
        return ApplyResult(applied=execution["applied"], dry_run=False, commands=commands, notes=notes)

    def _build_apply_commands(self, settings: AppSettingsPayload) -> list[str]:
        connection = settings.ethernet.interface or "eth0"
        commands = [f"hostnamectl set-hostname {settings.hostname}"]
        if settings.ethernet.mode == "static":
            commands.extend(
                [
                    f"nmcli connection modify {connection} ipv4.method manual",
                    f"nmcli connection modify {connection} ipv4.addresses {settings.ethernet.address}",
                    f"nmcli connection modify {connection} ipv4.gateway {settings.ethernet.gateway or ''}",
                    f"nmcli connection modify {connection} ipv4.dns {','.join(settings.ethernet.dns)}",
                ]
            )
        else:
            commands.extend(
                [
                    f"nmcli connection modify {connection} ipv4.method auto",
                    f"nmcli connection modify {connection} ipv4.addresses ''",
                    f"nmcli connection modify {connection} ipv4.gateway ''",
                    f"nmcli connection modify {connection} ipv4.dns ''",
                ]
            )
        if settings.wifi.mode == "client" and settings.wifi.ssid:
            commands.append(f"nmcli device wifi connect {settings.wifi.ssid} password <hidden>")
        commands.append(f"nmcli connection up {connection}")
        return commands

    def _execute_apply(self, settings: AppSettingsPayload) -> dict:
        notes = []
        if not self._runner.available("hostnamectl"):
            return {"applied": False, "notes": ["hostnamectl is not available on this host."]}
        if not self._runner.available("nmcli"):
            return {"applied": False, "notes": ["nmcli is not available on this host."]}

        hostname_result = self._runner.run(["hostnamectl", "set-hostname", settings.hostname])
        if not hostname_result.ok:
            return {"applied": False, "notes": [hostname_result.stderr.strip() or "Failed to set hostname."]}

        for command in self._nmcli_commands(settings):
            result = self._runner.run(command)
            if not result.ok:
                notes.append(result.stderr.strip() or f"Failed: {' '.join(command)}")
                return {"applied": False, "notes": notes}

        notes.append("Network settings applied.")
        return {"applied": True, "notes": notes}

    def _nmcli_commands(self, settings: AppSettingsPayload) -> list[list[str]]:
        connection = settings.ethernet.interface or "eth0"
        commands: list[list[str]] = []
        if settings.ethernet.mode == "static":
            commands.extend(
                [
                    ["nmcli", "connection", "modify", connection, "ipv4.method", "manual"],
                    ["nmcli", "connection", "modify", connection, "ipv4.addresses", settings.ethernet.address],
                    ["nmcli", "connection", "modify", connection, "ipv4.gateway", settings.ethernet.gateway],
                    ["nmcli", "connection", "modify", connection, "ipv4.dns", ",".join(settings.ethernet.dns)],
                ]
            )
        else:
            commands.extend(
                [
                    ["nmcli", "connection", "modify", connection, "ipv4.method", "auto"],
                    ["nmcli", "connection", "modify", connection, "ipv4.addresses", ""],
                    ["nmcli", "connection", "modify", connection, "ipv4.gateway", ""],
                    ["nmcli", "connection", "modify", connection, "ipv4.dns", ""],
                ]
            )
        if settings.wifi.mode == "client" and settings.wifi.ssid:
            wifi_command = ["nmcli", "device", "wifi", "connect", settings.wifi.ssid]
            if settings.wifi.password:
                wifi_command.extend(["password", settings.wifi.password])
            commands.append(wifi_command)
        commands.append(["nmcli", "connection", "up", connection])
        return commands

    def _detect_interfaces(self) -> list[dict]:
        if self._runner.available("ip"):
            result = self._runner.run(["ip", "-json", "addr"])
            if result.ok:
                payload = result.json() or []
                return [
                    {
                        "name": item.get("ifname", ""),
                        "state": item.get("operstate", "unknown"),
                        "addresses": [addr.get("local", "") for addr in item.get("addr_info", [])],
                    }
                    for item in payload
                ]
        return []

    def _active_connections(self) -> list[dict]:
        if not self._runner.available("nmcli"):
            return []
        result = self._runner.run(["nmcli", "-t", "-f", "NAME,DEVICE,TYPE,STATE", "connection", "show", "--active"])
        if not result.ok:
            return []
        connections = []
        for line in result.stdout.splitlines():
            parts = line.split(":")
            if len(parts) < 4:
                continue
            connections.append(
                {
                    "name": parts[0],
                    "device": parts[1],
                    "type": parts[2],
                    "state": ":".join(parts[3:]),
                }
            )
        return connections
