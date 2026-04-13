import asyncio
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

    def profile_status(self) -> list[dict]:
        profiles = self._store.load().serial_ports
        resolved_devices = self._resolve_profile_devices(profiles)
        return [
            {
                "index": index,
                "label": profile.label,
                "device_hint": profile.device_hint,
                "active_device": resolved_devices[index],
                "baud_rate": profile.baud_rate,
                "data_bits": profile.data_bits,
                "parity": profile.parity,
                "stop_bits": profile.stop_bits,
                "present": resolved_devices[index] is not None,
                "connected": False,
            }
            for index, profile in enumerate(profiles)
        ]

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
        resolved_device = self._resolve_profile_devices(profiles)[profile_index]
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

            log_path = self._create_session_log_path(profile, resolved_device)
            reader = asyncio.create_task(self._reader_loop(serial_handle, websocket, log_path))
            writer = asyncio.create_task(self._writer_loop(serial_handle, websocket, log_path))
            done, pending = await asyncio.wait({reader, writer}, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            serial_handle.close()
            self._active_websockets.pop(resolved_device, None)
            self._append_log_entry(
                log_path,
                "system",
                f"session closed for {profile.label} on {resolved_device}",
            )
            for task in done:
                exc = task.exception()
                if exc:
                    raise exc

    async def _reader_loop(self, serial_handle, websocket, log_path: Path) -> None:
        while True:
            data = await asyncio.to_thread(serial_handle.read, 1024)
            if data:
                decoded = data.decode(errors="replace")
                self._append_log_entry(log_path, "rx", decoded)
                await websocket.send_text(decoded)
            await asyncio.sleep(0.02)

    async def _writer_loop(self, serial_handle, websocket, log_path: Path) -> None:
        while True:
            message = await websocket.receive_text()
            self._append_log_entry(log_path, "tx", message)
            await asyncio.to_thread(serial_handle.write, message.encode())

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
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        safe_label = self._sanitize_path_part(profile.label)
        device_name = active_device or profile.device_hint
        safe_device = self._sanitize_path_part(Path(device_name).name or device_name)
        log_path = self._log_root / f"{timestamp}-{safe_label}-{safe_device}.log"
        self._append_log_entry(
            log_path,
            "system",
            f"session opened for {profile.label} on {device_name}",
        )
        return log_path

    def _append_log_entry(self, log_path: Path, direction: str, payload: str) -> None:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        lines = payload.splitlines() or [payload]
        with log_path.open("a", encoding="utf-8") as handle:
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

    def _resolve_profile_devices(self, profiles) -> list[str | None]:
        detected = self._detected_devices()
        remaining = detected.copy()
        resolved: list[str | None] = []
        for profile in profiles:
            selected = None
            if profile.device_hint in remaining:
                selected = profile.device_hint
                remaining.remove(profile.device_hint)
            elif remaining:
                selected = remaining.pop(0)
            resolved.append(selected)
        return resolved
