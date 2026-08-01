"""SelfMediaHub - FastAPI-Anwendung. Startpunkt für Container und lokal."""
import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, RedirectResponse

from . import config, db
from .routes import api, auth as auth_routes, health, pages
from .services import auth, providers, scheduler, tvdb, updatecheck


def _configure_logging() -> None:
    """Zentrale Logging-Config: eine Zeile je Ereignis nach stdout (docker logs),
    Stufe aus config.LOG_LEVEL. Laeuft beim Import, damit sie auch greift, wenn die
    App von einem externen ASGI-Server geladen wird (nicht nur ueber main())."""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )


_configure_logging()
logger = logging.getLogger("selfmediahub")

# Gueltige uvicorn-Log-Level; ungueltiges LOG_LEVEL faellt auf "info" zurueck.
_UVICORN_LEVELS = {"critical", "error", "warning", "info", "debug", "trace"}

# Immer erreichbar (auch ohne Anmeldung): statische Dateien + Health-Check.
_OPEN_PREFIXES = ("/static", "/api/health")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init_db()
    providers.ensure_fixed_providers()  # feste Dienste TMDb/TheTVDB sicherstellen
    _log_tvdb_key()
    scheduler.start()
    updatecheck.start()
    yield


def _log_tvdb_key() -> None:
    """Beim Start protokollieren, ob ein TheTVDB-Projekt-Key vorhanden ist und ob
    er noch funktioniert (Rotations-Kontrolle). Der Key selbst wird NICHT geloggt
    - nur die letzten 4 Zeichen zur Wiedererkennung."""
    key = providers.api_key_for("tvdb")
    if not key:
        logger.warning("Kein TheTVDB-Projekt-Key gefunden - TheTVDB-Anreicherung ist deaktiviert.")
        return
    try:
        ok, msg = tvdb.key_ok()
    except Exception as exc:  # noqa: BLE001 - Start darf nie am Key-Test scheitern
        ok, msg = False, str(exc)
    if ok:
        logger.info("TheTVDB-Projekt-Key geladen (…%s) - Test: OK", key[-4:])
    else:
        logger.error("TheTVDB-Projekt-Key geladen (…%s) - Test fehlgeschlagen (%s) - "
                     "Key evtl. rotieren", key[-4:], msg)


app = FastAPI(title=config.APP_NAME, version=config.VERSION, lifespan=lifespan)


class AuthMiddleware(BaseHTTPMiddleware):
    """Login-Wand: ohne gueltige Sitzung nur Login/Setup erreichbar.

    Kein Konto -> zur Ersteinrichtung zwingen. Auth deaktiviert oder
    SMH_DISABLE_AUTH gesetzt -> alles offen.
    """
    async def dispatch(self, request, call_next):
        path = request.url.path
        if path.startswith(_OPEN_PREFIXES) or config.DISABLE_AUTH:
            return await call_next(request)
        if not auth.account_exists():
            if path == "/setup":
                return await call_next(request)
            return _gate(request, "/setup")
        if auth.auth_enabled():
            if auth.verify_session(request.cookies.get(auth.SESSION_COOKIE)):
                return await call_next(request)
            if path == "/login":
                return await call_next(request)
            return _gate(request, "/login")
        return await call_next(request)


def _gate(request, to: str):
    """API -> 401 (JSON), Seiten -> Weiterleitung zur Login-/Setup-Seite."""
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": "Nicht angemeldet"}, status_code=401)
    return RedirectResponse(to, status_code=303)


app.add_middleware(AuthMiddleware)

_BASE = os.path.dirname(__file__)
app.mount("/static", StaticFiles(directory=os.path.join(_BASE, "static")), name="static")

app.include_router(health.router)
app.include_router(auth_routes.router)
app.include_router(api.router)
app.include_router(pages.router)


def main() -> None:
    import uvicorn

    logger.info("%s läuft auf http://0.0.0.0:%s", config.APP_NAME, config.PORT)
    level = config.LOG_LEVEL.lower()
    uvicorn.run(app, host="0.0.0.0", port=config.PORT,
                log_level=level if level in _UVICORN_LEVELS else "info")


if __name__ == "__main__":
    main()
