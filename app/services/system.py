from app.core.config import get_settings
from app.core.models import ApplyResult
from app.services.command_runner import CommandRunner
from app.services.settings_store import SettingsStore


class SystemService:
    """Boundary for system operations such as hostname and password changes."""

    def __init__(self) -> None:
        self._store = SettingsStore()
        self._runner = CommandRunner()
        self._settings = get_settings()

    def get_status(self) -> dict:
        settings = self._store.load()
        return {
            "hostname": settings.hostname,
            "default_user": "service",
            "password_change_supported": not self._settings.dry_run_system_changes,
            "dry_run": self._settings.dry_run_system_changes,
            "note": "System changes are dry-run by default.",
        }

    def change_password(self, current_password: str, new_password: str) -> bool:
        if current_password != "service":
            return False
        if len(new_password) < 4:
            return False
        if self._settings.dry_run_system_changes:
            return True
        if not self._runner.available("chpasswd"):
            return False
        result = self._runner.run_with_input(["chpasswd"], f"service:{new_password}\n")
        return result.ok

    def apply_hostname(self) -> ApplyResult:
        hostname = self._store.load().hostname
        command = f"hostnamectl set-hostname {hostname}"
        if self._settings.dry_run_system_changes:
            return ApplyResult(applied=False, dry_run=True, commands=[command], notes=["Dry-run mode enabled."])
        return ApplyResult(applied=False, dry_run=False, commands=[command], notes=["Execution path not enabled yet."])
