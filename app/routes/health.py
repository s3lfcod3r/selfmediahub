"""Health-/Status-Endpunkt für Monitoring und Container-Checks."""
from fastapi import APIRouter, Request

from .. import config, db
from ..services import auth, providers, sources

router = APIRouter()


def _may_see_details(request: Request) -> bool:
    """Betriebsdaten nur fuer eine gueltige Sitzung (oder wenn keine Anmeldung
    aktiv ist)."""
    if config.DISABLE_AUTH or not auth.auth_active():
        return True
    return bool(auth.verify_session(request.cookies.get(auth.SESSION_COOKIE)))


@router.get("/api/health")
def health(request: Request):
    """Ohne Anmeldung nur die Lebendmeldung.

    Der Endpunkt ist bewusst offen, damit Container-/Uptime-Checks ihn erreichen.
    Version, Sync-Stand, Anzahl der Eintraege und die Frage, welche Dienste
    konfiguriert sind, gehen Unangemeldete aber nichts an - eine Versionsnummer
    erleichtert gezielte Angriffe auf bekannte Luecken.
    """
    if not _may_see_details(request):
        return {"ok": True}
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
