"""Background poller that honours the server's "report requested" flag.

The web cannot push to a kit, so the kit polls a lightweight endpoint. When the
server says a report was requested, the kit posts an inventory-only report
(a stat walk, no manifest fetch or downloads) and the server clears the flag.
"""

import logging
import threading

logger = logging.getLogger(__name__)


class ReportRequestPoller:
    def __init__(self, service, interval_seconds: int = 60):
        self.service = service
        self.interval = max(15, int(interval_seconds))
        self._stop = threading.Event()
        self._thread = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._loop, name="fieldkit-report-poller", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _loop(self) -> None:
        while not self._stop.wait(self.interval):
            try:
                if self.service.report_requested():
                    self.service.report_now()
            except Exception as exc:  # noqa: BLE001 - a poll failure must not kill the thread
                logger.debug("Report poll failed: %s", exc)
