from pathlib import Path

from app.core.config import get_settings
from app.core.models import ApplyResult
from app.services.command_runner import CommandRunner
from app.services.settings_store import SettingsStore
from app.services.storage import StorageService


class TransferService:
    def __init__(self) -> None:
        self._store = SettingsStore()
        self._runtime = get_settings()
        self._runner = CommandRunner()
        self._storage = StorageService(self._runtime)

    def get_status(self) -> dict:
        settings = self._store.load()
        export_root = self._storage.export_root()
        configured = settings.transfer_services
        return {
            "root": str(export_root),
            "http_base": "/fieldkit",
            "libraries": [f"/fieldkit/{name}" for name in self._storage.export_library_paths()],
            "http_export": self._http_export_status(configured.http_export_enabled),
            "tftp": self._service_status("tftpd-hpa", configured.tftp_enabled),
            "ftp": self._service_status("vsftpd", configured.ftp_enabled),
            "scp": self._readonly_service_status("ssh"),
            "usb_gadget": self._usb_gadget_status(),
            "dry_run": self._runtime.dry_run_transfer_changes,
        }

    def apply_settings(self) -> ApplyResult:
        settings = self._store.load()
        configured = settings.transfer_services
        export_root = self._storage.sync_export_tree()
        commands = [
            f"export root {export_root}",
            "sudo -n /bin/bash /opt/fieldkit/scripts/install_transfer_services.sh",
            self._http_export_preview(configured.http_export_enabled),
            self._command_preview("tftpd-hpa", configured.tftp_enabled),
            self._command_preview("vsftpd", configured.ftp_enabled),
        ]
        if self._runtime.dry_run_transfer_changes:
            return ApplyResult(
                applied=False,
                dry_run=True,
                commands=commands,
                notes=["Dry-run mode enabled. Transfer service states were saved but not applied."],
            )

        notes = [f"Export root synced at {export_root}."]
        failures: list[str] = []
        install_result = self._runner.run(
            ["sudo", "-n", "/bin/bash", "/opt/fieldkit/scripts/install_transfer_services.sh"]
        )
        if not install_result.ok:
            failures.append(
                "transfer support: "
                + (install_result.stderr.strip() or install_result.stdout.strip() or "command failed")
            )
        http_export_result = self._apply_http_export(configured.http_export_enabled)
        if http_export_result.ok:
            notes.append(f"http export {'enabled' if configured.http_export_enabled else 'disabled'} on port 80.")
        else:
            failures.append(f"http export: {http_export_result.stderr.strip() or http_export_result.stdout.strip() or 'command failed'}")
        if not failures:
            for unit, enabled in (("tftpd-hpa", configured.tftp_enabled), ("vsftpd", configured.ftp_enabled)):
                result = self._apply_unit(unit, enabled)
                if result.ok:
                    notes.append(f"{unit} {'enabled' if enabled else 'disabled'}.")
                else:
                    failures.append(f"{unit}: {result.stderr.strip() or result.stdout.strip() or 'command failed'}")

        return ApplyResult(
            applied=not failures,
            dry_run=False,
            commands=commands,
            notes=notes + failures,
        )

    def _service_status(self, unit: str, configured_enabled: bool) -> dict:
        if self._runtime.dry_run_transfer_changes:
            return {
                "configured_enabled": configured_enabled,
                "active": False,
                "enabled": configured_enabled,
                "manageable": False,
                "note": "Dry-run mode enabled.",
            }

        active = self._runner.run(["sudo", "-n", "systemctl", "is-active", unit])
        enabled = self._runner.run(["sudo", "-n", "systemctl", "is-enabled", unit])
        active_state = active.stdout.strip()
        enabled_state = enabled.stdout.strip()
        manageable = active.ok or enabled.ok or active_state in {"active", "inactive"} or enabled_state in {"enabled", "disabled"}
        return {
            "configured_enabled": configured_enabled,
            "active": active_state == "active",
            "enabled": enabled_state == "enabled",
            "manageable": manageable,
            "note": "" if manageable else (active.stderr.strip() or enabled.stderr.strip() or "Service status unavailable."),
        }

    def _apply_unit(self, unit: str, enabled: bool):
        if enabled:
            return self._runner.run(["sudo", "-n", "systemctl", "enable", "--now", unit])
        return self._runner.run(["sudo", "-n", "systemctl", "disable", "--now", unit])

    def _command_preview(self, unit: str, enabled: bool) -> str:
        action = "enable --now" if enabled else "disable --now"
        return f"sudo -n systemctl {action} {unit}"

    def _http_export_preview(self, enabled: bool) -> str:
        return f"sudo -n /bin/bash /opt/fieldkit/scripts/install_export_http_mode.sh (EXPORT_HTTP_ENABLED={1 if enabled else 0})"

    def _apply_http_export(self, enabled: bool):
        return self._runner.run(
            [
                "sudo",
                "-n",
                "/bin/bash",
                "/opt/fieldkit/scripts/install_export_http_mode.sh",
            ],
            env={
                "EXPORT_HTTP_ENABLED": "1" if enabled else "0",
            },
        )

    def _http_export_status(self, configured_enabled: bool) -> dict:
        rendered = self._read_text(Path("/etc/nginx/sites-enabled/fieldkit"))
        export_http_active = "listen 80;" in rendered and (
            "location ^~ /fieldkit" in rendered
            or ("proxy_pass http://127.0.0.1:8000;" in rendered and "return 301 https://$host$request_uri;" not in rendered)
        )
        note = "" if rendered else "nginx config unavailable."
        return {
            "configured_enabled": configured_enabled,
            "active": export_http_active,
            "manageable": bool(rendered),
            "note": note,
        }

    def _readonly_service_status(self, unit: str) -> dict:
        if self._runtime.dry_run_transfer_changes:
            return {
                "active": False,
                "enabled": False,
                "manageable": False,
                "note": "Dry-run mode enabled.",
            }

        active = self._runner.run(["sudo", "-n", "systemctl", "is-active", unit])
        enabled = self._runner.run(["sudo", "-n", "systemctl", "is-enabled", unit])
        active_state = active.stdout.strip()
        enabled_state = enabled.stdout.strip()
        manageable = active.ok or enabled.ok or active_state in {"active", "inactive"} or enabled_state in {"enabled", "disabled"}
        return {
            "active": active_state == "active",
            "enabled": enabled_state == "enabled",
            "manageable": manageable,
            "note": "" if manageable else (active.stderr.strip() or enabled.stderr.strip() or "Service status unavailable."),
        }

    def _usb_gadget_status(self) -> dict:
        model = self._read_text(Path("/proc/device-tree/model")).replace("\x00", "").strip()
        udc_entries = self._list_dir_names(Path("/sys/class/udc"))
        supported = bool(udc_entries)
        note = (
            "USB gadget export requires an OTG-capable Raspberry Pi port. This appliance does not expose a USB device controller."
            if not supported
            else "USB gadget hardware appears present. A future implementation could present Fieldkit exports as a USB device."
        )
        return {
            "supported": supported,
            "model": model or "Unknown Raspberry Pi",
            "controllers": udc_entries,
            "note": note,
        }

    def _read_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return ""

    def _list_dir_names(self, path: Path) -> list[str]:
        try:
            return sorted(entry.name for entry in path.iterdir())
        except OSError:
            return []
