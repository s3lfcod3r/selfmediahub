"""Benachrichtigungen über einen generischen JSON-Webhook (best-effort).

Kompatibel mit ntfy-Bridges, Discord-Webhooks, Apprise-Endpunkten usw.
"""
import requests

from .. import config

TIMEOUT = 10


def send(event: str, message: str, extra: dict = None) -> bool:
    """JSON an den Webhook posten. Fehler werden geschluckt (nie sync-blockend)."""
    url = config.NOTIFY_WEBHOOK_URL
    if not url:
        return False
    payload = {"app": config.APP_NAME, "event": event, "message": message}
    if extra:
        payload.update(extra)
    try:
        requests.post(url, json=payload, timeout=TIMEOUT)
        return True
    except requests.RequestException:
        return False
