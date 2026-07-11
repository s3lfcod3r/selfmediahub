"""SelfMediaHub - FastAPI-Anwendung. Startpunkt für Container und lokal."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import config, db
from .routes import api, health, pages
from .services import scheduler, updatecheck


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init_db()
    scheduler.start()
    updatecheck.start()
    yield


app = FastAPI(title=config.APP_NAME, version=config.VERSION, lifespan=lifespan)

_BASE = os.path.dirname(__file__)
app.mount("/static", StaticFiles(directory=os.path.join(_BASE, "static")), name="static")

app.include_router(health.router)
app.include_router(api.router)
app.include_router(pages.router)


def main() -> None:
    import uvicorn

    print(f"{config.APP_NAME} läuft auf http://0.0.0.0:{config.PORT}", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=config.PORT)


if __name__ == "__main__":
    main()
