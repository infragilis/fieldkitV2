from app.core.config import get_settings
from app.core.models import ApplyResult
from app.services.command_runner import CommandRunner
from app.services.settings_store import SettingsStore


class SystemService:
    """Boundary for system operations such as hostname and password changes."""

    _THROTTLED_UNDERVOLTAGE_NOW = 0x1
    _THROTTLED_UNDERVOLTAGE_SEEN = 0x10000

    def __init__(self) -> None:
        self._store = SettingsStore()
        self._runner = CommandRunner()
        self._settings = get_settings()

    def get_status(self) -> dict:
        settings = self._store.load()
        shell_user = "service"
        try:
            import getpass

            shell_user = getpass.getuser() or shell_user
        except (ImportError, OSError):
            pass
        return {
            "hostname": settings.hostname,
            "default_user": shell_user,
            "local_shell_user": shell_user,
            "password_change_supported": not self._settings.dry_run_system_changes,
            "dry_run": self._settings.dry_run_system_changes,
            "note": (
                "System changes are dry-run by default."
                if self._settings.dry_run_system_changes
                else "Live system changes are enabled."
            ),
            "power": self._power_status(),
        }

    def change_password(self, current_password: str, new_password: str) -> bool:
        if len(new_password) < 4:
            return False
        if self._settings.dry_run_system_changes:
            return bool(current_password)
        if not self._runner.available("sudo"):
            return False
        result = self._runner.run_with_input(
            ["sudo", "-n", "/bin/bash", "/opt/fieldkit/scripts/change_password.sh", "service", current_password, new_password],
            None,
        )
        return result.ok

    def apply_hostname(self) -> ApplyResult:
        hostname = self._store.load().hostname
        command = f"sudo -n /bin/bash /opt/fieldkit/scripts/set_appliance_hostname.sh {hostname}"
        if self._settings.dry_run_system_changes:
            return ApplyResult(applied=False, dry_run=True, commands=[command], notes=["Dry-run mode enabled."])
        if not self._runner.available("sudo"):
            return ApplyResult(applied=False, dry_run=False, commands=[command], notes=["sudo is not available on this host."])
        result = self._runner.run(
            ["sudo", "-n", "/bin/bash", "/opt/fieldkit/scripts/set_appliance_hostname.sh", hostname]
        )
        if not result.ok:
            return ApplyResult(
                applied=False,
                dry_run=False,
                commands=[command],
                notes=[result.stderr.strip() or result.stdout.strip() or "Failed to set hostname."],
            )
        return ApplyResult(applied=True, dry_run=False, commands=[command], notes=["Hostname applied."])

    def _power_status(self) -> dict:
        if not self._runner.available("vcgencmd"):
            return {
                "supported": False,
                "input_voltage_ok": None,
                "undervoltage_now": False,
                "undervoltage_seen": False,
                "raw": "",
                "label": "unavailable",
            }
        result = self._runner.run(["vcgencmd", "get_throttled"])
        if not result.ok:
            return {
                "supported": False,
                "input_voltage_ok": None,
                "undervoltage_now": False,
                "undervoltage_seen": False,
                "raw": result.stdout.strip() or result.stderr.strip(),
                "label": "unavailable",
            }
        raw = result.stdout.strip()
        value = self._parse_throttled_value(raw)
        undervoltage_now = bool(value & self._THROTTLED_UNDERVOLTAGE_NOW)
        undervoltage_seen = bool(value & self._THROTTLED_UNDERVOLTAGE_SEEN)
        input_voltage_ok = not undervoltage_now
        if undervoltage_now:
            label = "low now"
        elif undervoltage_seen:
            label = "stable now, low seen"
        else:
            label = "ok"
        return {
            "supported": True,
            "input_voltage_ok": input_voltage_ok,
            "undervoltage_now": undervoltage_now,
            "undervoltage_seen": undervoltage_seen,
            "raw": raw,
            "label": label,
        }

    @staticmethod
    def _parse_throttled_value(raw: str) -> int:
        _, _, value = raw.partition("=")
        value = value.strip() or "0x0"
        try:
            return int(value, 16)
        except ValueError:
            return 0
