from pathlib import Path
from typing import BinaryIO

from app.core.config import RuntimeSettings


def ensure_runtime_layout(settings: RuntimeSettings) -> None:
    for path in (
        settings.content_root / settings.data_dir_name,
        settings.content_root / settings.personal_dir_name,
        settings.content_root / settings.usb_dir_name,
        settings.state_root,
        settings.state_root / settings.serial_log_dir_name,
    ):
        path.mkdir(parents=True, exist_ok=True)


class StorageService:
    def __init__(self, settings: RuntimeSettings) -> None:
        self.settings = settings
        ensure_runtime_layout(settings)

    def library_paths(self) -> dict[str, Path]:
        usb_path = self._detect_usb_mount() or (self.settings.content_root / self.settings.usb_dir_name)
        return {
            "data": self.settings.content_root / self.settings.data_dir_name,
            "personal": self.settings.content_root / self.settings.personal_dir_name,
            "usb": usb_path,
            "serial-logs": self.settings.state_root / self.settings.serial_log_dir_name,
        }

    def list_library(self, library: str, relative_path: str = "") -> dict:
        base = self.resolve_download(library, relative_path) if relative_path else self._library_root(library)
        if not base.exists():
            raise FileNotFoundError(relative_path)
        if not base.is_dir():
            raise NotADirectoryError(relative_path)
        items = []
        seen_paths: set[str] = set()
        for entry in sorted(base.iterdir(), key=lambda path: (not path.is_dir(), path.name.lower())):
            if entry.name.startswith("."):
                continue
            relative_entry_path = str(entry.relative_to(self._library_root(library)))
            dedupe_key = str(entry.resolve(strict=False))
            if dedupe_key in seen_paths or relative_entry_path in seen_paths:
                continue
            seen_paths.add(dedupe_key)
            seen_paths.add(relative_entry_path)
            items.append(
                {
                    "name": entry.name,
                    "is_dir": entry.is_dir(),
                    "size": entry.stat().st_size,
                    "path": relative_entry_path,
                    "deletable": self._is_deletable_library(library) and entry.is_file(),
                }
            )
        return {"library": library, "path": str(base.relative_to(self._library_root(library))), "items": items}

    def save_personal_upload(self, filename: str, stream: BinaryIO) -> Path:
        return self.save_upload("personal", filename, stream)

    def save_upload(self, library: str, filename: str, stream: BinaryIO) -> Path:
        if not self._is_uploadable_library(library):
            raise ValueError(f"Uploads are not allowed for library: {library}")
        target = self._library_root(library) / Path(filename).name
        if target.exists():
            raise FileExistsError(Path(filename).name)
        with target.open("wb") as output:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                output.write(chunk)
        return target

    def resolve_download(self, library: str, relative_path: str) -> Path:
        root = self._library_root(library).resolve()
        target = (root / relative_path).resolve()
        if root not in target.parents and target != root:
            raise ValueError("Invalid path")
        return target

    def delete_file(self, library: str, relative_path: str) -> None:
        if not self._is_deletable_library(library):
            raise ValueError(f"Deletes are not allowed for library: {library}")
        target = self.resolve_download(library, relative_path)
        if not target.exists():
            raise FileNotFoundError(relative_path)
        if not target.is_file():
            raise ValueError("Only files can be deleted")
        target.unlink()

    def _library_root(self, library: str) -> Path:
        paths = self.library_paths()
        if library not in paths:
            raise ValueError(f"Unknown library: {library}")
        return paths[library]

    def _is_deletable_library(self, library: str) -> bool:
        return library in {"personal", "serial-logs"}

    def _is_uploadable_library(self, library: str) -> bool:
        return library in {"personal", "usb"}

    def _detect_usb_mount(self) -> Path | None:
        candidates = (
            Path("/media/service"),
            Path("/media"),
            Path("/mnt"),
        )
        for base in candidates:
            if not base.exists():
                continue
            for path in sorted(base.glob("*")):
                if path.is_dir() and not path.name.startswith("."):
                    if base.name == "media" and path.name == "service":
                        for nested in sorted(path.glob("*")):
                            if nested.is_dir() and not nested.name.startswith("."):
                                return nested
                        continue
                    return path
        return None
