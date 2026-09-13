import json
import os
import tempfile

from app.core.config import get_settings
from app.core.models import AppSettingsPayload


class SettingsStore:
    def __init__(self) -> None:
        self.runtime = get_settings()
        self.path = self.runtime.state_root / self.runtime.settings_file

    def load(self) -> AppSettingsPayload:
        if not self.path.exists():
            payload = AppSettingsPayload()
            payload.server_sync.base_url = self.runtime.server_base_url
            self.save(payload)
            return payload
        return AppSettingsPayload.model_validate_json(self.path.read_text())

    def save(self, payload: AppSettingsPayload) -> AppSettingsPayload:
        directory = self.path.parent
        directory.mkdir(parents=True, exist_ok=True)
        # settings.json holds the device token and Wi-Fi PSK: keep it private
        # and write atomically so a crash cannot leave a truncated file.
        try:
            os.chmod(directory, 0o700)
        except OSError:
            pass
        descriptor, temp_path = tempfile.mkstemp(dir=directory, prefix=".settings-", suffix=".tmp")
        try:
            with os.fdopen(descriptor, "w") as handle:
                json.dump(payload.model_dump(), handle, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temp_path, 0o600)
            os.replace(temp_path, self.path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        self._sync_dir(directory)
        return payload

    @staticmethod
    def _sync_dir(path) -> None:
        try:
            descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        except OSError:
            return
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
