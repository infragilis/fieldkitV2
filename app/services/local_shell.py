import asyncio
import fcntl
import json
import os
import pty
import select
import signal
import struct
import subprocess
import termios
from pathlib import Path


class LocalShellService:
    """Browser-accessible local shell running as the web-service user."""

    async def stream_shell(self, websocket) -> None:
        master_fd, slave_fd = pty.openpty()
        self._set_window_size(master_fd, cols=120, rows=32)
        env = {
            **os.environ,
            "TERM": "xterm-256color",
            "HOME": str(Path.home()),
            "SHELL": os.environ.get("SHELL", "/bin/bash"),
            "PS1": "service@fieldkit:$ ",
            "PROMPT_COMMAND": "bind 'set enable-bracketed-paste off' >/dev/null 2>&1",
            "INPUTRC": "/dev/null",
        }
        process = subprocess.Popen(
            [env["SHELL"], "--noprofile", "--norc", "-i"],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            cwd=Path.home(),
            env=env,
            start_new_session=True,
            close_fds=True,
        )
        os.close(slave_fd)

        reader = asyncio.create_task(self._reader_loop(master_fd, process, websocket))
        writer = asyncio.create_task(self._writer_loop(master_fd, process, websocket))
        done, pending = await asyncio.wait({reader, writer}, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        try:
            process.terminate()
            await asyncio.wait_for(asyncio.to_thread(process.wait), timeout=1.0)
        except (subprocess.SubprocessError, TimeoutError):
            process.kill()
        finally:
            os.close(master_fd)
        for task in done:
            exc = task.exception()
            if exc:
                raise exc

    async def _reader_loop(self, master_fd: int, process: subprocess.Popen, websocket) -> None:
        while process.poll() is None:
            data = await asyncio.to_thread(self._read_available, master_fd)
            if data:
                await websocket.send_text(data.decode(errors="replace"))
            else:
                await asyncio.sleep(0.02)

    async def _writer_loop(self, master_fd: int, process: subprocess.Popen, websocket) -> None:
        while True:
            message = await websocket.receive_text()
            payload = self._parse_message(message)
            if payload["type"] == "resize":
                self._set_window_size(master_fd, cols=payload["cols"], rows=payload["rows"])
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGWINCH)
                continue
            os.write(master_fd, payload["data"].encode())

    def _parse_message(self, message: str) -> dict:
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            return {"type": "input", "data": message}
        if payload.get("type") == "resize":
            cols = max(2, int(payload.get("cols", 80)))
            rows = max(1, int(payload.get("rows", 24)))
            return {"type": "resize", "cols": cols, "rows": rows}
        return {"type": "input", "data": str(payload.get("data", ""))}

    def _read_available(self, master_fd: int) -> bytes:
        ready, _, _ = select.select([master_fd], [], [], 0.1)
        if not ready:
            return b""
        try:
            return os.read(master_fd, 4096)
        except OSError:
            return b""

    def _set_window_size(self, master_fd: int, cols: int, rows: int) -> None:
        packed = struct.pack("HHHH", rows, cols, 0, 0)
        fcntl.ioctl(master_fd, termios.TIOCSWINSZ, packed)
