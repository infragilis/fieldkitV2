import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path

from app.services.settings_store import SettingsStore

try:
    import serial
    from serial import SerialException
except ImportError:  # pragma: no cover
    serial = None
    SerialException = Exception


class SerialService:
    """Serial discovery plus optional live WebSocket-backed console sessions."""

    _serial_by_id_root = Path("/dev/serial/by-id")
    _serial_by_path_root = Path("/dev/serial/by-path")

    def __init__(self) -> None:
        self._store = SettingsStore()
        self._runtime = self._store.runtime
        self._log_root = self._runtime.state_root / self._runtime.serial_log_dir_name
        self._locks: dict[str, asyncio.Lock] = {}
        self._active_websockets: dict[str, object] = {}

    def list_ports(self) -> list[dict]:
        ports = [{"device": device, "present": True} for device in self._detected_devices()]
        if not ports:
            for profile in self._store.load().serial_ports:
                ports.append({"device": profile.device_hint, "present": False})
        return ports

    def list_adapters(self) -> list[dict]:
        """Detected serial adapters with their stable identity (by-id/by-path)."""
        return [self._adapter_public(adapter) for adapter in self._detected_adapters()]

    def profile_status(self) -> list[dict]:
        profiles = self._store.load().serial_ports
        adapters = self._resolve_profile_adapters(profiles)
        statuses = []
        for index, profile in enumerate(profiles):
            adapter = adapters[index]
            statuses.append(
                {
                    "index": index,
                    "label": profile.label,
                    "device_hint": profile.device_hint,
                    "active_device": self._open_device(adapter),
                    "tty_device": adapter["tty"] if adapter else None,
                    "stable_device": (adapter["by_id"] or adapter["by_path"]) if adapter else None,
                    "serial": adapter["serial"] if adapter else None,
                    "bound": bool(adapter and profile.device_hint.strip()),
                    "baud_rate": profile.baud_rate,
                    "data_bits": profile.data_bits,
                    "parity": profile.parity,
                    "stop_bits": profile.stop_bits,
                    "present": adapter is not None,
                    "connected": False,
                }
            )
        return statuses

    def session_status(self) -> list[dict]:
        statuses = self.profile_status()
        active_devices = set(self._active_websockets)
        for status in statuses:
            status["connected"] = status["active_device"] in active_devices
        return statuses

    async def reset_console(self, profile_index: int) -> bool:
        profiles = self._store.load().serial_ports
        if profile_index < 0 or profile_index >= len(profiles):
            raise ValueError("Invalid console index")
        resolved_device = self._resolve_profile_devices(profiles)[profile_index]
        if resolved_device is None:
            return False
        websocket = self._active_websockets.get(resolved_device)
        if websocket is None:
            return False
        await websocket.close(code=1012)
        return True

    async def stream_console(self, profile_index: int, websocket) -> None:
        profiles = self._store.load().serial_ports
        if profile_index < 0 or profile_index >= len(profiles):
            await websocket.send_text("Invalid console index.\n")
            await websocket.close(code=1008)
            return

        profile = profiles[profile_index]
        adapter = self._resolve_profile_adapters(profiles)[profile_index]
        resolved_device = self._open_device(adapter)
        if resolved_device is None:
            await websocket.send_text("No serial adapter detected for this console.\n")
            await websocket.close(code=1011)
            return

        lock = self._locks.setdefault(resolved_device, asyncio.Lock())
        if lock.locked():
            await websocket.send_text("Console already in use.\n")
            await websocket.close(code=1013)
            return

        async with lock:
            self._active_websockets[resolved_device] = websocket
            if serial is None:
                await websocket.send_text("pyserial is not installed.\n")
                await websocket.close()
                self._active_websockets.pop(resolved_device, None)
                return

            try:
                serial_handle = serial.Serial(
                    port=resolved_device,
                    baudrate=profile.baud_rate,
                    bytesize=profile.data_bits,
                    parity=self._parity(profile.parity),
                    stopbits=profile.stop_bits,
                    timeout=0.1,
                )
            except (SerialException, ValueError) as exc:
                await websocket.send_text(f"Failed to open {resolved_device}: {exc}\n")
                await websocket.close(code=1011)
                self._active_websockets.pop(resolved_device, None)
                return

            log_path = self._create_session_log_path(profile, adapter["tty"] if adapter else resolved_device)
            log_handle = log_path.open("a", encoding="utf-8")
            reader = asyncio.create_task(self._reader_loop(serial_handle, websocket, log_handle))
            writer = asyncio.create_task(self._writer_loop(serial_handle, websocket, log_handle))
            done, pending = await asyncio.wait({reader, writer}, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            serial_handle.close()
            self._active_websockets.pop(resolved_device, None)
            self._append_log_entry(
                log_handle,
                "system",
                f"session closed for {profile.label} on {resolved_device}",
            )
            log_handle.close()
            for task in done:
                exc = task.exception()
                if exc:
                    raise exc

    async def _reader_loop(self, serial_handle, websocket, log_handle) -> None:
        while True:
            data = await asyncio.to_thread(serial_handle.read, 1024)
            if data:
                decoded = data.decode(errors="replace")
                self._append_log_entry(log_handle, "rx", decoded)
                await websocket.send_text(decoded)
            await asyncio.sleep(0.02)

    async def _writer_loop(self, serial_handle, websocket, log_handle) -> None:
        while True:
            message = await websocket.receive_text()
            self._append_log_entry(log_handle, "tx", message)
            await asyncio.to_thread(self._write_serial_payload, serial_handle, message)

    def _write_serial_payload(self, serial_handle, message: str) -> None:
        serial_handle.write(message.encode())

    def _parity(self, parity: str) -> str:
        if serial is None:
            return "N"
        mapping = {
            "none": serial.PARITY_NONE,
            "even": serial.PARITY_EVEN,
            "odd": serial.PARITY_ODD,
        }
        return mapping.get(parity, serial.PARITY_NONE)

    def _create_session_log_path(self, profile, active_device: str | None = None) -> Path:
        self._log_root.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self._log_root, 0o700)
        except OSError:
            pass
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        safe_label = self._sanitize_path_part(profile.label)
        device_name = active_device or profile.device_hint
        safe_device = self._sanitize_path_part(Path(device_name).name or device_name)
        log_path = self._log_root / f"{timestamp}-{safe_label}-{safe_device}.log"
        suffix = 0
        while True:
            candidate = log_path if suffix == 0 else self._log_root / f"{timestamp}-{safe_label}-{safe_device}-{suffix}.log"
            try:
                descriptor = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                log_path = candidate
                break
            except FileExistsError:
                suffix += 1
        with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
            self._append_log_entry(
                handle,
                "system",
                f"session opened for {profile.label} on {device_name}",
            )
        return log_path

    def _append_log_entry(self, handle, direction: str, payload: str) -> None:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        lines = payload.splitlines() or [payload]
        for line in lines:
            handle.write(f"[{timestamp}] {direction.upper()} {line}\n")

    def _sanitize_path_part(self, value: str) -> str:
        cleaned = "".join(char if char.isalnum() else "-" for char in value.strip().lower())
        return cleaned.strip("-") or "session"

    def _detected_devices(self) -> list[str]:
        devices: list[str] = []
        for pattern in ("ttyUSB*", "ttyACM*"):
            for candidate in sorted(Path("/dev").glob(pattern)):
                devices.append(str(candidate))
        return devices

    def _detected_adapters(self) -> list[dict]:
        """Detected adapters keyed to their stable /dev/serial identity.

        Stable symlinks let a console profile survive the kernel renumbering
        ttyUSB* across reboots or re-plugs. Adapters without a unique serial
        still fall back to their tty path (and by-path when present).
        """
        by_id = self._stable_symlink_map(self._serial_by_id_root)
        by_path = self._stable_symlink_map(self._serial_by_path_root)
        adapters = []
        for tty in self._detected_devices():
            resolved = self._resolve_device_path(tty)
            stable_id = by_id.get(resolved)
            path_id = by_path.get(resolved)
            serial = self._read_usb_serial(tty)
            adapters.append(
                {
                    "tty": tty,
                    "by_id": stable_id,
                    "by_path": path_id,
                    "serial": serial,
                    "label": self._adapter_label(stable_id or path_id, tty, serial),
                }
            )
        return adapters

    def _adapter_public(self, adapter: dict) -> dict:
        return {
            "tty": adapter["tty"],
            "by_id": adapter["by_id"],
            "by_path": adapter["by_path"],
            "serial": adapter["serial"],
            "label": adapter["label"],
            "present": True,
        }

    @staticmethod
    def _adapter_label(stable_id: str | None, tty: str, serial: str | None) -> str:
        if stable_id:
            name = Path(stable_id).name
            if name.startswith("usb-"):
                name = name[4:]
            if name.endswith("-if00-port0"):
                name = name[: -len("-if00-port0")]
            return f"{name} ({tty})"
        if serial:
            return f"USB serial {serial} ({tty})"
        return tty

    @staticmethod
    def _resolve_device_path(device: str) -> str:
        try:
            return str(Path(device).resolve())
        except OSError:
            return device

    def _stable_symlink_map(self, root: Path) -> dict[str, str]:
        mapping: dict[str, str] = {}
        try:
            entries = sorted(root.iterdir())
        except OSError:
            return mapping
        for entry in entries:
            try:
                target = str(entry.resolve())
            except OSError:
                continue
            # The Pi kernel exposes both -usb- and -usbv2- by-path variants;
            # keep whichever appears first (sorted) to avoid duplicates.
            mapping.setdefault(target, str(entry))
        return mapping

    @staticmethod
    def _read_usb_serial(device: str) -> str | None:
        base = Path("/sys/class/tty") / Path(device).name / "device"
        try:
            current = base.resolve()
        except OSError:
            return None
        for _ in range(5):
            try:
                value = (current / "serial").read_text().strip()
            except OSError:
                value = ""
            if value:
                return value
            parent = current.parent
            if parent == current:
                return None
            current = parent
        return None

    def _open_device(self, adapter: dict | None) -> str | None:
        if adapter is None:
            return None
        return adapter["by_id"] or adapter["by_path"] or adapter["tty"]

    def _adapter_matches(self, adapter: dict, hint: str) -> bool:
        hint = hint.strip()
        if not hint:
            return False
        candidates = {
            adapter["tty"],
            adapter["by_id"],
            adapter["by_path"],
            adapter["serial"],
            self._resolve_device_path(adapter["tty"]),
        }
        if hint in candidates:
            return True
        try:
            if Path(hint).exists() and Path(hint).resolve() == Path(adapter["tty"]).resolve():
                return True
        except OSError:
            pass
        return False

    def _resolve_profile_adapters(self, profiles) -> list[dict | None]:
        remaining = self._detected_adapters()
        resolved: list[dict | None] = [None] * len(profiles)

        for index, profile in enumerate(profiles):
            hint = (profile.device_hint or "").strip()
            if not hint:
                continue
            for adapter in remaining:
                if self._adapter_matches(adapter, hint):
                    resolved[index] = adapter
                    remaining.remove(adapter)
                    break

        # Only blank profiles auto-assign. A profile with an explicit pin that
        # did not match stays unbound (present: false) so it can never silently
        # open a different physical cable.
        for index, profile in enumerate(profiles):
            if resolved[index] is not None:
                continue
            if (profile.device_hint or "").strip():
                continue
            if remaining:
                resolved[index] = remaining.pop(0)

        return resolved

    def _resolve_profile_devices(self, profiles) -> list[str | None]:
        return [self._open_device(adapter) for adapter in self._resolve_profile_adapters(profiles)]
