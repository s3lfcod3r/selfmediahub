"""Health-/Status-Endpunkt fuer Monitoring und Container-Checks."""
from fastapi import APIRouter

from .. import config, db

router = APIRouter()


@router.get("/api/health")
def health():
    return {
        "ok": True,
        "app": config.APP_NAME,
        "version": config.VERSION,
        "emby_configured": config.emby_configured(),
        "last_sync": db.get_meta("last_sync"),
        "item_count": db.get_meta("last_sync_count"),
    }
