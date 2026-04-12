import json

from app.core.config import get_settings
from app.core.models import AppSettingsPayload


class SettingsStore:
    def __init__(self) -> None:
        self.runtime = get_settings()
        self.path = self.runtime.state_root / self.runtime.settings_file

    def load(self) -> AppSettingsPayload:
        if not self.path.exists():
            payload = AppSettingsPayload()
            self.save(payload)
            return payload
        return AppSettingsPayload.model_validate_json(self.path.read_text())

    def save(self, payload: AppSettingsPayload) -> AppSettingsPayload:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload.model_dump(), indent=2))
        return payload
