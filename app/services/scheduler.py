"""Optionaler Hintergrund-Scan: alle N Stunden automatisch neu einlesen."""
import threading
import time

from .. import config
from . import sync as sync_service

_thread = None


def _loop() -> None:
    interval = max(300, int(config.SCAN_INTERVAL_HOURS * 3600))
    while True:
        time.sleep(interval)
        try:
            sync_service.run_sync()
        except Exception:  # noqa: BLE001 - Hintergrundlauf darf nie crashen
            pass


def start() -> None:
    global _thread
    if config.SCAN_INTERVAL_HOURS <= 0:
        return
    if _thread and _thread.is_alive():
        return
    _thread = threading.Thread(target=_loop, name="smh-scan", daemon=True)
    _thread.start()
