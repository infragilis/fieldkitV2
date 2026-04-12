import json
import os
import shutil
import subprocess
from dataclasses import dataclass

from app.core.config import get_settings


@dataclass
class CommandResult:
    ok: bool
    command: list[str]
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0

    def json(self):
        if not self.stdout:
            return None
        return json.loads(self.stdout)


class CommandRunner:
    def __init__(self) -> None:
        self.settings = get_settings()

    def available(self, binary: str) -> bool:
        return shutil.which(binary) is not None

    def run(self, command: list[str], env: dict[str, str] | None = None) -> CommandResult:
        return self.run_with_input(command, None, env=env)

    def run_with_input(self, command: list[str], stdin_text: str | None, env: dict[str, str] | None = None) -> CommandResult:
        try:
            completed = subprocess.run(
                command,
                input=stdin_text,
                capture_output=True,
                text=True,
                timeout=self.settings.command_timeout_seconds,
                check=False,
                env=None if env is None else {**os.environ, **env},
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return CommandResult(ok=False, command=command, stderr=str(exc), returncode=1)

        return CommandResult(
            ok=completed.returncode == 0,
            command=command,
            stdout=completed.stdout,
            stderr=completed.stderr,
            returncode=completed.returncode,
        )
