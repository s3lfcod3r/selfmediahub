"""Import/Scan: liest die konfigurierte Quelle und legt die Daten lokal ab."""
from datetime import datetime, timezone

from .. import config, db
from ..connectors.emby import EmbyConnector


def build_connector():
    """Den Connector der aktuell konfigurierten Quelle bauen (oder None)."""
    if config.emby_configured():
        return EmbyConnector(config.EMBY_URL, config.EMBY_API_KEY)
    return None


def run_sync() -> dict:
    """Vollen Re-Sync ausfuehren. Gibt {count, at} zurueck."""
    connector = build_connector()
    if connector is None:
        raise RuntimeError(
            "Keine Medienquelle konfiguriert (EMBY_URL / EMBY_API_KEY setzen)."
        )
    items = connector.fetch_items()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    db.replace_source_items(connector.kind, items, now)
    db.set_meta("last_sync", now)
    db.set_meta("last_sync_count", str(len(items)))
    return {"count": len(items), "at": now}
