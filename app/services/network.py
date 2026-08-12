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
            "wifi_access_point": self._wifi_ap_status(settings),
            "applied": False,
            "dry_run": self._settings.dry_run_system_changes,
            "note": (
                "Live network apply is enabled."
                if not self._settings.dry_run_system_changes
                else "Apply actions are prepared, but host network changes remain dry-run by default."
            ),
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
        return []

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
        commands = [
            f"sudo -n /bin/bash /opt/fieldkit/scripts/set_appliance_hostname.sh {settings.hostname}",
            "sudo -n /bin/bash /opt/fieldkit/scripts/install_wifi_ap_support.sh",
        ]
        for command in self._ethernet_commands(settings):
            commands.append(" ".join(command))
        commands.append(" ".join(self._wifi_apply_command(settings)))
        if settings.wifi.mode != "ap":
            connection = self._resolve_ethernet_connection(settings)
            commands.append(f"sudo -n nmcli connection up {connection}")
        return commands

    def _execute_apply(self, settings: AppSettingsPayload) -> dict:
        notes = []
        if not self._runner.available("hostnamectl"):
            return {"applied": False, "notes": ["hostnamectl is not available on this host."]}
        if not self._runner.available("nmcli"):
            return {"applied": False, "notes": ["nmcli is not available on this host."]}

        connection = self._resolve_ethernet_connection(settings)

        hostname_result = self._runner.run(
            ["sudo", "-n", "/bin/bash", "/opt/fieldkit/scripts/set_appliance_hostname.sh", settings.hostname]
        )
        if not hostname_result.ok:
            return {"applied": False, "notes": [hostname_result.stderr.strip() or "Failed to set hostname."]}

        install_result = self._runner.run(
            ["sudo", "-n", "/bin/bash", "/opt/fieldkit/scripts/install_wifi_ap_support.sh"]
        )
        if not install_result.ok:
            return {
                "applied": False,
                "notes": [install_result.stderr.strip() or install_result.stdout.strip() or "Failed to install Wi-Fi AP support."],
            }

        for command in self._ethernet_commands(settings):
            result = self._runner.run(command)
            if not result.ok:
                notes.append(result.stderr.strip() or f"Failed: {' '.join(command)}")
                return {"applied": False, "notes": notes}

        wifi_result = self._apply_wifi_mode(settings)
        if not wifi_result.ok:
            notes.append(wifi_result.stderr.strip() or wifi_result.stdout.strip() or "Failed to apply Wi-Fi mode.")
            return {"applied": False, "notes": notes}

        if settings.wifi.mode != "ap":
            result = self._runner.run(["sudo", "-n", "nmcli", "connection", "up", connection])
            if not result.ok:
                notes.append(result.stderr.strip() or f"Failed: nmcli connection up {connection}")
                return {"applied": False, "notes": notes}

        notes.append("Network settings applied.")
        return {"applied": True, "notes": notes}

    def _ethernet_commands(self, settings: AppSettingsPayload) -> list[list[str]]:
        connection = self._resolve_ethernet_connection(settings)
        commands: list[list[str]] = []
        if settings.ethernet.mode == "static":
            commands.append(
                [
                    "sudo",
                    "-n",
                    "nmcli",
                    "connection",
                    "modify",
                    connection,
                    "ipv4.method",
                    "manual",
                    "ipv4.addresses",
                    settings.ethernet.address,
                    "ipv4.gateway",
                    settings.ethernet.gateway,
                    "ipv4.dns",
                    ",".join(settings.ethernet.dns),
                ]
            )
        else:
            commands.extend(
                [
                    ["sudo", "-n", "nmcli", "connection", "modify", connection, "ipv4.method", "auto"],
                    ["sudo", "-n", "nmcli", "connection", "modify", connection, "ipv4.addresses", ""],
                    ["sudo", "-n", "nmcli", "connection", "modify", connection, "ipv4.gateway", ""],
                    ["sudo", "-n", "nmcli", "connection", "modify", connection, "ipv4.dns", ""],
                ]
            )
        return commands

    def _resolve_ethernet_connection(self, settings: AppSettingsPayload) -> str:
        interface = settings.ethernet.interface or "eth0"
        result = self._runner.run(["nmcli", "-g", "GENERAL.CONNECTION", "device", "show", interface])
        if result.ok:
            connection = result.stdout.strip()
            if connection and connection != "--":
                return connection
        return interface

    def _apply_wifi_mode(self, settings: AppSettingsPayload):
        return self._runner.run(self._wifi_apply_command(settings))

    def _wifi_apply_command(self, settings: AppSettingsPayload) -> list[str]:
        command = [
            "sudo",
            "-n",
            "/bin/bash",
            "/opt/fieldkit/scripts/apply_wifi_mode.sh",
            settings.wifi.mode,
            "wlan0",
        ]
        if settings.wifi.mode == "client" and settings.wifi.ssid:
            command.extend(
                [
                    settings.wifi.ssid,
                    settings.wifi.password or "",
                    settings.wifi.country_code,
                    settings.wifi.ssid,
                    settings.wifi.password or "",
                ]
            )
        elif settings.wifi.mode == "ap":
            command.extend(
                [
                    settings.wifi.ssid or "fieldkit",
                    settings.wifi.password or "fieldkit",
                    settings.wifi.country_code,
                ]
            )
        return command

    def _wifi_ap_status(self, settings: AppSettingsPayload) -> dict:
        hostapd = self._runner.run(["sudo", "-n", "systemctl", "is-active", "fieldkit-ap-hostapd"])
        dnsmasq = self._runner.run(["sudo", "-n", "systemctl", "is-active", "fieldkit-ap-dnsmasq"])
        return {
            "configured_mode": settings.wifi.mode,
            "ssid": settings.wifi.ssid or "fieldkit",
            "hostapd_active": hostapd.stdout.strip() == "active",
            "dnsmasq_active": dnsmasq.stdout.strip() == "active",
            "manageable": hostapd.ok or dnsmasq.ok,
            "note": "" if (hostapd.ok or dnsmasq.ok) else (hostapd.stderr.strip() or dnsmasq.stderr.strip()),
        }

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
