from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


class RuntimeSettings(BaseModel):
    app_name: str = "fieldkit"
    content_root: Path = Path("runtime/content")
    state_root: Path = Path("runtime/state")
    data_dir_name: str = "data"
    personal_dir_name: str = "personal"
    usb_dir_name: str = "usb"
    settings_file: str = "settings.json"
    command_timeout_seconds: float = 5.0
    dry_run_system_changes: bool = True


@lru_cache
def get_settings() -> RuntimeSettings:
    return RuntimeSettings()
