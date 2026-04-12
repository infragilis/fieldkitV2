import asyncio
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
        self._locks: dict[str, asyncio.Lock] = {}

    def list_ports(self) -> list[dict]:
        ports = []
        for pattern in ("ttyUSB*", "ttyACM*"):
            for candidate in sorted(Path("/dev").glob(pattern)):
                ports.append({"device": str(candidate), "present": True})
        if not ports:
            for profile in self._store.load().serial_ports:
                ports.append({"device": profile.device_hint, "present": False})
        return ports

    def profile_status(self) -> list[dict]:
        detected = {entry["device"] for entry in self.list_ports() if entry["present"]}
        return [
            {
                "index": index,
                "label": profile.label,
                "device_hint": profile.device_hint,
                "baud_rate": profile.baud_rate,
                "data_bits": profile.data_bits,
                "parity": profile.parity,
                "stop_bits": profile.stop_bits,
                "present": profile.device_hint in detected,
                "connected": False,
            }
            for index, profile in enumerate(self._store.load().serial_ports)
        ]

    def session_status(self) -> list[dict]:
        return self.profile_status()

    async def stream_console(self, profile_index: int, websocket) -> None:
        profiles = self._store.load().serial_ports
        if profile_index < 0 or profile_index >= len(profiles):
            await websocket.send_text("Invalid console index.\n")
            await websocket.close(code=1008)
            return

        profile = profiles[profile_index]
        lock = self._locks.setdefault(profile.device_hint, asyncio.Lock())
        if lock.locked():
            await websocket.send_text("Console already in use.\n")
            await websocket.close(code=1013)
            return

        async with lock:
            if serial is None:
                await websocket.send_text("pyserial is not installed.\n")
                await websocket.close()
                return

            try:
                serial_handle = serial.Serial(
                    port=profile.device_hint,
                    baudrate=profile.baud_rate,
                    bytesize=profile.data_bits,
                    parity=self._parity(profile.parity),
                    stopbits=profile.stop_bits,
                    timeout=0.1,
                )
            except (SerialException, ValueError) as exc:
                await websocket.send_text(f"Failed to open {profile.device_hint}: {exc}\n")
                await websocket.close(code=1011)
                return

            reader = asyncio.create_task(self._reader_loop(serial_handle, websocket))
            writer = asyncio.create_task(self._writer_loop(serial_handle, websocket))
            done, pending = await asyncio.wait({reader, writer}, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            serial_handle.close()
            for task in done:
                exc = task.exception()
                if exc:
                    raise exc

    async def _reader_loop(self, serial_handle, websocket) -> None:
        while True:
            data = await asyncio.to_thread(serial_handle.read, 1024)
            if data:
                await websocket.send_text(data.decode(errors="replace"))
            await asyncio.sleep(0.02)

    async def _writer_loop(self, serial_handle, websocket) -> None:
        while True:
            message = await websocket.receive_text()
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
