import os
import shutil
import stat
from pathlib import Path
from typing import BinaryIO

from app.core.config import RuntimeSettings

DATA_SUBDIRECTORIES = ("cisco", "ontap", "brocade", "efos", "nvidia")

# Cap appliance-side uploads (0 disables the cap). Server-published vendor files
# are placed directly on the server, not through this client upload path.
MAX_UPLOAD_BYTES = int(os.environ.get("FIELDKIT_MAX_UPLOAD_BYTES", str(10 * 1024**3)) or "0")


def ensure_runtime_layout(settings: RuntimeSettings) -> None:
    for path in (
        settings.content_root / settings.data_dir_name,
        settings.content_root / settings.personal_dir_name,
        settings.content_root / settings.usb_dir_name,
        settings.content_root / settings.export_dir_name,
        settings.state_root,
        settings.state_root / settings.serial_log_dir_name,
    ):
        path.mkdir(parents=True, exist_ok=True)
    for name in DATA_SUBDIRECTORIES:
        (settings.content_root / settings.data_dir_name / name).mkdir(parents=True, exist_ok=True)


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

    def export_library_paths(self) -> dict[str, Path]:
        paths = self.library_paths()
        return {name: path for name, path in paths.items() if name != "serial-logs"}

    def export_root(self) -> Path:
        return self.settings.content_root / self.settings.export_dir_name

    def sync_export_tree(self) -> Path:
        root = self.export_root()
        root.mkdir(parents=True, exist_ok=True)
        export_libraries = self.export_library_paths()
        for library, source in export_libraries.items():
            self._sync_export_directory(root / library, source)
        for stale_entry in root.iterdir():
            if stale_entry.name not in export_libraries:
                self._remove_tree(stale_entry)
        return root

    def resolve_export_path(self, relative_path: str = "") -> Path:
        root = self.export_root().resolve()
        if not relative_path:
            return root

        parts = [part for part in Path(relative_path).parts if part not in {"", "."}]
        if any(part == ".." for part in parts):
            raise ValueError("Invalid path")
        if any(part.startswith(".") for part in parts):
            raise ValueError("Invalid path")
        if not parts:
            return root

        library = parts[0]
        library_roots = self.export_library_paths()
        if library not in library_roots:
            raise ValueError("Invalid path")

        target = library_roots[library].resolve()
        if len(parts) > 1:
            target = (target / Path(*parts[1:])).resolve()
        if library_roots[library].resolve() not in target.parents and target != library_roots[library].resolve():
            raise ValueError("Invalid path")
        return target

    def list_export_path(self, relative_path: str = "") -> dict:
        base = self.resolve_export_path(relative_path)
        if not base.exists():
            raise FileNotFoundError(relative_path)
        if not base.is_dir():
            raise NotADirectoryError(relative_path)
        root = self.export_root().resolve()
        current_path = self._export_relative_path(relative_path)
        items = []
        for entry in sorted(base.iterdir(), key=lambda path: (not path.is_dir(), path.name.lower())):
            if entry.name.startswith("."):
                continue
            item_relative = "/".join(part for part in (current_path, entry.name) if part)
            items.append(
                {
                    "name": entry.name,
                    "is_dir": entry.is_dir(),
                    "path": item_relative,
                    "size": entry.stat().st_size,
                }
            )
        return {"path": current_path, "items": items}

    def list_library(self, library: str, relative_path: str = "") -> dict:
        root = self._library_root(library).resolve()
        base = self.resolve_download(library, relative_path) if relative_path else root
        if not base.exists():
            raise FileNotFoundError(relative_path)
        if not base.is_dir():
            raise NotADirectoryError(relative_path)
        items = []
        seen_paths: set[str] = set()
        for entry in sorted(base.iterdir(), key=lambda path: (not path.is_dir(), path.name.lower())):
            if entry.name.startswith("."):
                continue
            relative_entry_path = str(entry.relative_to(root))
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
        return {"library": library, "path": str(base.relative_to(root)), "items": items}

    def save_personal_upload(self, filename: str, stream: BinaryIO) -> Path:
        return self.save_upload("personal", filename, stream)

    def save_upload(self, library: str, filename: str, stream: BinaryIO) -> Path:
        if not self._is_uploadable_library(library):
            raise ValueError(f"Uploads are not allowed for library: {library}")
        name = Path(filename).name
        target = self._library_root(library) / name
        if target.exists():
            raise FileExistsError(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        free = shutil.disk_usage(target.parent).free
        temp = target.parent / f".{name}.upload-{os.getpid()}"
        written = 0
        try:
            with temp.open("wb") as output:
                while True:
                    chunk = stream.read(1024 * 1024)
                    if not chunk:
                        break
                    written += len(chunk)
                    if MAX_UPLOAD_BYTES and written > MAX_UPLOAD_BYTES:
                        raise ValueError("Upload exceeds the maximum allowed size")
                    if written + 64 * 1024 * 1024 > free:
                        raise ValueError("Not enough disk space for this upload")
                    output.write(chunk)
            os.replace(temp, target)
        finally:
            if temp.exists():
                temp.unlink(missing_ok=True)
        if library in self.export_library_paths():
            self.sync_export_tree()
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
        if library in self.export_library_paths():
            self.sync_export_tree()

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

    def _sync_export_directory(self, export_dir: Path, source: Path) -> None:
        if export_dir.is_symlink() or export_dir.is_file():
            export_dir.unlink()
        export_dir.mkdir(parents=True, exist_ok=True)

        source_root = source.resolve()
        seen_names: set[str] = set()
        for entry in sorted(source.iterdir(), key=lambda path: path.name.lower()):
            if entry.name.startswith("."):
                continue
            entry_stat = entry.lstat()
            if os.path.islink(entry) or not self._is_under(entry.resolve(strict=False), source_root):
                raise ValueError(f"Refusing to export unsafe path: {entry}")
            seen_names.add(entry.name)
            target = export_dir / entry.name
            if stat_is_directory(entry_stat):
                self._sync_export_directory(target, entry)
            else:
                self._sync_export_file(target, entry)

        for stale_entry in export_dir.iterdir():
            if stale_entry.name not in seen_names:
                self._remove_tree(stale_entry)

    def _sync_export_file(self, export_path: Path, source: Path) -> None:
        if source.is_symlink():
            raise ValueError(f"Refusing to export symlink: {source}")
        if export_path.is_symlink() or export_path.is_dir():
            self._remove_tree(export_path)
        try:
            source_stat = source.lstat()
        except OSError:
            return
        if export_path.exists():
            try:
                export_stat = export_path.stat()
            except OSError:
                export_stat = None
            if export_stat is not None:
                same_inode = export_stat.st_dev == source_stat.st_dev and export_stat.st_ino == source_stat.st_ino
                if same_inode:
                    return  # already hardlinked
                if export_stat.st_dev == source_stat.st_dev:
                    # Same filesystem: replace the redundant copy with a hardlink.
                    export_path.unlink()
                elif export_stat.st_size == source_stat.st_size and export_stat.st_mtime_ns == source_stat.st_mtime_ns:
                    return  # cross-device copy already up to date
                else:
                    export_path.unlink()
        # Hardlink shares the inode (no duplicated bytes); fall back to a copy
        # across filesystems or where hardlinks are unsupported (e.g. vfat USB).
        try:
            os.link(source, export_path)
        except OSError:
            shutil.copy2(source, export_path)

    def _remove_tree(self, path: Path) -> None:
        if path.is_symlink() or path.is_file():
            path.unlink()
            return
        if path.is_dir():
            for child in path.iterdir():
                self._remove_tree(child)
            path.rmdir()

    def _export_relative_path(self, relative_path: str) -> str:
        if not relative_path:
            return ""
        parts = [part for part in Path(relative_path).parts if part not in {"", "."}]
        if any(part == ".." for part in parts):
            raise ValueError("Invalid path")
        return "/".join(parts)

    @staticmethod
    def _is_under(path: Path, root: Path) -> bool:
        return path == root or root in path.parents


def stat_is_directory(stat_result: os.stat_result) -> bool:
    """Avoid following a symlink after the lstat safety check."""
    return stat.S_ISDIR(stat_result.st_mode)
