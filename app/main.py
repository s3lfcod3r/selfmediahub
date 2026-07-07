"""SelfMediaHub - FastAPI-Anwendung. Startpunkt fuer Container und lokal."""
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import config, db
from .routes import api, health, pages

app = FastAPI(title=config.APP_NAME, version=config.VERSION)

_BASE = os.path.dirname(__file__)
app.mount("/static", StaticFiles(directory=os.path.join(_BASE, "static")), name="static")

app.include_router(health.router)
app.include_router(api.router)
app.include_router(pages.router)


@app.on_event("startup")
def _startup() -> None:
    db.init_db()


def main() -> None:
    import uvicorn

    print(f"{config.APP_NAME} laeuft auf http://0.0.0.0:{config.PORT}", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=config.PORT)


if __name__ == "__main__":
    main()
