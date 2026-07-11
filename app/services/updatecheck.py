"""Update-Pruefung gegen die neueste GitHub-Release-Version.

Laeuft im Hintergrund (beim Start + einmal taeglich) und legt das Ergebnis in
``app_meta`` ab. Der Seitenaufruf liest nur diesen Cache - also kein Live-Call
beim Laden. Faellt nie hart aus (Hintergrundlauf darf nie crashen).
"""
import threading
import time
from datetime import datetime, timezone

import requests

from .. import config, db

_API = "https://api.github.com/repos/{repo}/releases/latest"
_CHECK_INTERVAL = 24 * 3600  # taeglich
_thread = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_version(text) -> tuple:
    """'v0.3.0' / '0.3.0' -> (0, 3, 0); nicht-numerische Teile werden zu 0."""
    nums = []
    for part in str(text).lstrip("vV").split("."):
        digits = "".join(ch for ch in part if ch.isdigit())
        nums.append(int(digits) if digits else 0)
    return tuple(nums) or (0,)


def _is_newer(latest, current) -> bool:
    a, b = _parse_version(latest), _parse_version(current)
    n = max(len(a), len(b))
    a += (0,) * (n - len(a))
    b += (0,) * (n - len(b))
    return a > b


def check_now() -> dict:
    """Live gegen GitHub pruefen und Ergebnis in app_meta ablegen. Best-effort."""
    latest, url = None, ""
    try:
        resp = requests.get(
            _API.format(repo=config.GITHUB_REPO),
            headers={"Accept": "application/vnd.github+json"}, timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            latest = (data.get("tag_name") or "").lstrip("vV") or None
            url = data.get("html_url") or ""
    except requests.RequestException:
        pass
    available = bool(latest and _is_newer(latest, config.VERSION))
    db.set_meta("update_latest", latest or "")
    db.set_meta("update_url", url)
    db.set_meta("update_available", "1" if available else "0")
    db.set_meta("update_checked_at", _now())
    return get_status()


def get_status() -> dict:
    """Zwischengespeicherten Update-Status lesen (kein Netzwerkzugriff)."""
    latest = db.get_meta("update_latest") or ""
    return {
        "current": config.VERSION,
        "latest": latest or None,
        "available": db.get_meta("update_available") == "1",
        "url": db.get_meta("update_url") or f"https://github.com/{config.GITHUB_REPO}/releases",
        "checked_at": db.get_meta("update_checked_at") or "",
    }


def _loop() -> None:
    while True:
        try:
            check_now()
        except Exception:  # noqa: BLE001 - Hintergrundlauf darf nie crashen
            pass
        time.sleep(_CHECK_INTERVAL)


def start() -> None:
    global _thread
    if _thread and _thread.is_alive():
        return
    _thread = threading.Thread(target=_loop, name="smh-update", daemon=True)
    _thread.start()
