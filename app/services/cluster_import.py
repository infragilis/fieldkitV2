"""Facade orchestrating workbook parse -> validate, plus minimal audit logging."""

import json
from datetime import datetime, timezone

from app.core.config import get_settings
from app.core.models import AnsibleGeneration, ClusterConfig, ParseResult
from app.services.cluster_ansible import generate
from app.services.cluster_mappings import MAPPING_VERSION
from app.services.cluster_parser import detect_template, extract_fields, open_workbook
from app.services.cluster_validation import validate


class ClusterImportService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._audit_path = self._settings.state_root / "cluster-import-audit.log"

    def parse(self, filename: str, data: bytes) -> ParseResult:
        workbook = open_workbook(data, filename)
        template = detect_template(workbook)
        matches = extract_fields(workbook)
        config, issues = validate(matches, filename, template, MAPPING_VERSION)
        self._audit("parse", filename, {"matches": len(matches), "issues": len(issues)})
        return ParseResult(config=config, matches=matches, issues=issues)

    def generate(self, config: ClusterConfig) -> AnsibleGeneration:
        result = generate(config)
        self._audit("generate", config.source.filename, {"draft": result.draft})
        return result

    def _audit(self, action: str, filename: str, detail: dict) -> None:
        # Audit only the action and counts; never the extracted values or
        # credentials.
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "filename": filename,
            **detail,
        }
        try:
            self._audit_path.parent.mkdir(parents=True, exist_ok=True)
            with self._audit_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry) + "\n")
        except OSError:
            pass
