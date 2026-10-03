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

# Headroom kept free on a removable device so the final write cannot fill it.
USB_COPY_MARGIN = 64 * 1024 * 1024


class UsbError(RuntimeError):
    """Base class for USB copy failures surfaced to the UI."""


class UsbNotMounted(UsbError):
    pass


class UsbSpaceError(UsbError):
    pass


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
        # Removable storage (`usb`) is a copy *destination*, not an export
        # source: mirroring it would copy the whole stick onto the appliance's
        # boot card, and a cross-device copy cannot be hardlinked. serial-logs
        # are diagnostics and are likewise never exported.
        paths = self.library_paths()
        return {name: path for name, path in paths.items() if name not in {"serial-logs", "usb"}}

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
        usb_root = self._detect_usb_mount() if library in {"data", "personal"} else None
        for entry in sorted(base.iterdir(), key=lambda path: (not path.is_dir(), path.name.lower())):
            if entry.name.startswith("."):
                continue
            relative_entry_path = str(entry.relative_to(root))
            dedupe_key = str(entry.resolve(strict=False))
            if dedupe_key in seen_paths or relative_entry_path in seen_paths:
                continue
            seen_paths.add(dedupe_key)
            seen_paths.add(relative_entry_path)
            on_usb = False
            if usb_root is not None:
                destination = self._usb_destination(usb_root, library, tuple(Path(relative_entry_path).parts))
                on_usb = destination.is_dir() if entry.is_dir() else destination.is_file()
            items.append(
                {
                    "name": entry.name,
                    "is_dir": entry.is_dir(),
                    "size": entry.stat().st_size,
                    "path": relative_entry_path,
                    "deletable": self._is_deletable_library(library) and entry.is_file(),
                    "on_usb": on_usb,
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

    def usb_mounted(self) -> bool:
        """True when a real removable device is mounted (not the local fallback)."""
        return self._detect_usb_mount() is not None

    def usb_destination_parts(self, library: str, rel_parts: tuple[str, ...]) -> tuple[str, ...]:
        """Map a library-relative path to its path on the USB device.

        The library path is preserved, except ONTAP payloads, which are placed in
        the USB root (``data/ontap/x`` -> ``x``).
        """
        if library == "data" and rel_parts and rel_parts[0] == "ontap":
            return rel_parts[1:]
        return rel_parts

    def _usb_destination(self, usb_root: Path, library: str, rel_parts: tuple[str, ...]) -> Path:
        parts = self.usb_destination_parts(library, rel_parts)
        return usb_root.joinpath(*parts) if parts else usb_root

    def copy_to_usb(self, library: str, relative_path: str, progress=None) -> dict:
        """Copy a file or folder from a library onto the mounted USB device.

        The source path under its library root is preserved on the USB
        (``data/brocade/x`` -> ``<usb>/brocade/x``), except ONTAP payloads, which
        land in the USB root (``data/ontap/x`` -> ``<usb>/x``). Files are copied
        to a temporary name and atomically renamed, so a partial copy never
        replaces a good file. The export mirror is not touched: ``usb`` is not an
        export source, so a copy is not written back onto the appliance's card.
        """
        if library not in {"data", "personal"}:
            raise ValueError("Choose the data or personal library as the source")
        source_root = self._library_root(library).resolve()
        source = self.resolve_download(library, relative_path)
        if not source.exists():
            raise FileNotFoundError(relative_path)
        if source.is_symlink():
            raise ValueError("Refusing to copy a symlink")
        usb_root = self._detect_usb_mount()
        if usb_root is None:
            raise UsbNotMounted("No USB storage is mounted on the kit.")
        usb_root = usb_root.resolve()

        rel_parts = self.usb_destination_parts(library, source.relative_to(source_root).parts)

        planned = self._plan_usb_copy(source, rel_parts)
        if not planned:
            raise ValueError("Nothing to copy (the folder is empty or holds only hidden files)")
        total_bytes = sum(size for _, _, size in planned)
        if total_bytes and shutil.disk_usage(usb_root).free < total_bytes + USB_COPY_MARGIN:
            raise UsbSpaceError("Not enough free space on the USB device.")

        copied = 0
        replaced = 0
        for src, dest_rel, size in planned:
            target = usb_root.joinpath(*dest_rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                replaced += 1
            temp = target.parent / f".{target.name}.copy-{os.getpid()}"
            try:
                shutil.copyfile(src, temp)
                with temp.open("rb") as handle:
                    os.fsync(handle.fileno())
                os.replace(temp, target)
            finally:
                temp.unlink(missing_ok=True)
            copied += size
            if progress is not None:
                progress({
                    "copied_bytes": copied,
                    "total_bytes": total_bytes,
                    "current_file": src.name,
                })
        return {
            "library": library,
            "path": relative_path,
            "usb_root": str(usb_root),
            "destination": str(Path(*rel_parts)) if rel_parts else "USB root",
            "files": len(planned),
            "bytes": total_bytes,
            "replaced": replaced,
        }

    def _plan_usb_copy(self, source: Path, rel_parts: tuple[str, ...]) -> list[tuple[Path, tuple[str, ...], int]]:
        """Return ``(source_file, destination_parts, size)`` rows for a copy."""
        if source.is_file():
            dest = rel_parts if rel_parts else (source.name,)
            return [(source, dest, source.stat().st_size)]
        base = Path(*rel_parts).parts if rel_parts else ()
        planned: list[tuple[Path, tuple[str, ...], int]] = []
        for path in sorted(source.rglob("*")):
            if path.is_symlink():
                raise ValueError(f"Refusing to copy symlink: {path.name}")
            if not path.is_file():
                continue
            parts = path.relative_to(source).parts
            if any(part.startswith(".") for part in parts):
                continue
            planned.append((path, base + parts, path.stat().st_size))
        return planned

    def _library_root(self, library: str) -> Path:
        paths = self.library_paths()
        if library not in paths:
            raise ValueError(f"Unknown library: {library}")
        return paths[library]

    def _is_deletable_library(self, library: str) -> bool:
        return library in {"personal", "usb", "serial-logs"}

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
