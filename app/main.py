"""SelfMediaHub - FastAPI-Anwendung. Startpunkt für Container und lokal."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, RedirectResponse

from . import config, db
from .routes import api, auth as auth_routes, health, pages
from .services import auth, providers, scheduler, updatecheck

# Immer erreichbar (auch ohne Anmeldung): statische Dateien + Health-Check.
_OPEN_PREFIXES = ("/static", "/api/health")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init_db()
    providers.ensure_fixed_providers()  # feste Dienste TMDb/TheTVDB sicherstellen
    scheduler.start()
    updatecheck.start()
    yield


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

    print(f"{config.APP_NAME} läuft auf http://0.0.0.0:{config.PORT}", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=config.PORT)


if __name__ == "__main__":
    main()
