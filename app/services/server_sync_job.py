"""One background sync at a time, with live progress and durable last outcome."""

import copy
import json
import logging
import os
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from app.services.server_sync import sync_error

logger = logging.getLogger(__name__)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class SyncInterrupted(Exception):
    pass


class ServerSyncJob:
    def __init__(self, service):
        self.service = service
        self.path = service._runtime.state_root / "server-sync-status.json"
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread = None
        self._started = None
        self._state = {"current_sync": None, "last_sync": None, "last_success_at": None}
        try:
            saved = json.loads(self.path.read_text())
            if isinstance(saved, dict):
                for key in ("current_sync", "last_sync"):
                    if isinstance(saved.get(key), dict):
                        self._state[key] = saved[key]
                if isinstance(saved.get("last_success_at"), str):
                    self._state["last_success_at"] = saved["last_success_at"]
        except (OSError, ValueError):
            pass
        interrupted = self._state["current_sync"]
        if isinstance(interrupted, dict):
            interrupted.update({"outcome": "interrupted", "finished_at": utc_now(), "error": "The appliance or web service restarted during this sync."})
            self._state.update(current_sync=None, last_sync=interrupted)
            self._save()

    def status(self):
        with self._lock:
            state = copy.deepcopy(self._state)
            current = state["current_sync"]
            if current is not None:
                current["elapsed_seconds"] = round(time.monotonic() - self._started)
                # A stalled connection must not display a misleading countdown.
                if time.monotonic() - self._last_progress > 10:
                    current["eta_seconds"] = None
                    current["bytes_per_second"] = 0
            return {"running": current is not None, **state}

    def start(self, trigger="manual") -> bool:
        with self._lock:
            if self._state["current_sync"] is not None:
                return False
            self._stop.clear()
            self._started = self._last_progress = time.monotonic()
            self._state["current_sync"] = {
                "started_at": utc_now(), "trigger": trigger, "phase": "starting",
                "total_files": None, "completed_files": 0, "total_bytes": None,
                "processed_bytes": 0, "downloaded_bytes": 0, "current_file": None,
                "current_file_bytes": 0, "current_file_size": None,
                "bytes_per_second": 0, "eta_seconds": None,
                "counts": {"ok": 0, "skipped": 0, "failed": 0},
            }
            self._save()
            self._thread = threading.Thread(target=self._run, name="fieldkit-server-sync", daemon=True)
            self._thread.start()
            return True

    def _progress(self, update):
        if self._stop.is_set():
            raise SyncInterrupted()
        with self._lock:
            self._last_progress = time.monotonic()
            self._state["current_sync"].update(update)

    def _run(self):
        result = {}
        error = None
        try:
            result = self.service.sync(progress=self._progress)
            outcome = "partial" if result["counts"]["failed"] or result.get("report_error") else "success"
        except SyncInterrupted:
            outcome, error = "interrupted", "Sync stopped because the web service is shutting down."
        except Exception as exc:
            outcome, error = "failed", sync_error(exc)
            logger.warning("Server sync failed (%s)", type(exc).__name__)
        with self._lock:
            last = {**self._state["current_sync"], **result}
            last.update(outcome=outcome, error=error, finished_at=utc_now(), elapsed_seconds=round(time.monotonic() - self._started))
            # Keep a bounded detailed summary without truncating the totals.
            if "files" in last:
                last["files"] = last["files"][:200]
            self._state.update(current_sync=None, last_sync=last)
            if outcome == "success":
                self._state["last_success_at"] = last["finished_at"]
            self._save()

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _save(self):
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", dir=self.path.parent, prefix=".sync-status-", delete=False) as output:
                temporary = Path(output.name)
                json.dump(self._state, output)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, self.path)
        except OSError:
            logger.warning("Could not persist server-sync status")
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
