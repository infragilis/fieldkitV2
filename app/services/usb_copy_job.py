"""One background USB copy at a time, with live progress.

Copying multi-gigabyte firmware onto a removable device can outlast an HTTP
request, so the route starts a worker thread and the page polls for progress.
Status is in-memory: a copy is user-initiated and quick to repeat, and a service
restart cannot leave a half-written file in place because the copy is written to
a temporary name and only renamed when complete.
"""

import copy
import threading
import time
from datetime import datetime, timezone

from app.services.storage import StorageService, UsbError


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class UsbCopyJob:
    def __init__(self, storage: StorageService) -> None:
        self.storage = storage
        self._lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._started = None
        self._state = {"current": None, "last": None}

    def status(self) -> dict:
        with self._lock:
            state = copy.deepcopy(self._state)
            if state["current"] is not None:
                state["current"]["elapsed_seconds"] = round(time.monotonic() - self._started)
            return {"running": state["current"] is not None, **state}

    def start(self, library: str, path: str) -> tuple[bool, str | None]:
        with self._lock:
            if self._state["current"] is not None:
                return False, "A USB copy is already running."
            self._started = time.monotonic()
            self._state["current"] = {
                "library": library,
                "path": path,
                "started_at": _utc_now(),
                "phase": "copying",
                "copied_bytes": 0,
                "total_bytes": None,
                "current_file": None,
            }
            self._thread = threading.Thread(
                target=self._run, args=(library, path), name="fieldkit-usb-copy", daemon=True
            )
            self._thread.start()
            return True, None

    def _progress(self, update: dict) -> None:
        with self._lock:
            if self._state["current"] is not None:
                self._state["current"].update(update)

    def _run(self, library: str, path: str) -> None:
        result: dict = {}
        error = None
        outcome = "success"
        try:
            result = self.storage.copy_to_usb(library, path, progress=self._progress)
        except UsbError as exc:
            outcome, error = "failed", str(exc)
        except FileNotFoundError:
            outcome, error = "failed", "The selected file no longer exists."
        except ValueError as exc:
            outcome, error = "failed", str(exc)
        except OSError as exc:
            outcome, error = "failed", f"The copy could not be written to the USB device ({exc.strerror or exc})."
        except Exception as exc:  # pragma: no cover - defensive
            outcome, error = "failed", f"Copy failed ({type(exc).__name__})."
        with self._lock:
            last = {**(self._state["current"] or {}), **result}
            last.update(
                outcome=outcome,
                error=error,
                finished_at=_utc_now(),
                elapsed_seconds=round(time.monotonic() - self._started),
            )
            self._state.update(current=None, last=last)

    def stop(self) -> None:
        if self._thread is not None:
            self._thread.join(timeout=5)
