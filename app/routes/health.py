"""Health-/Status-Endpunkt für Monitoring und Container-Checks."""
from fastapi import APIRouter

from .. import config, db
from ..services import providers, sources

router = APIRouter()


@router.get("/api/health")
def health():
    return {
        "ok": True,
        "app": config.APP_NAME,
        "version": config.VERSION,
        "emby_configured": sources.emby_enabled(),
        # Nur Vorhandensein (kein Netzabruf hier); der Live-Test laeuft beim Start.
        "tvdb_key": bool(providers.api_key_for("tvdb")),
        "last_sync": db.get_meta("last_sync"),
        "item_count": db.get_meta("last_sync_count"),
    }
