from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


class RuntimeSettings(BaseModel):
    app_name: str = "fieldkit"
    content_root: Path = Path("runtime/content")
    state_root: Path = Path("runtime/state")
    export_dir_name: str = "fieldkit"
    serial_log_dir_name: str = "serial-logs"
    data_dir_name: str = "data"
    personal_dir_name: str = "personal"
    usb_dir_name: str = "usb"
    settings_file: str = "settings.json"
    command_timeout_seconds: float = 30.0
    dry_run_system_changes: bool = False
    dry_run_transfer_changes: bool = False


@lru_cache
def get_settings() -> RuntimeSettings:
    return RuntimeSettings()
