"""JSON-API: Aktionen, die das Frontend per fetch() aufruft."""
from fastapi import APIRouter, HTTPException

from ..services import sync as sync_service

router = APIRouter(prefix="/api")


@router.post("/sync")
def api_sync():
    """Vollen Re-Sync der konfigurierten Quelle ausloesen."""
    try:
        result = sync_service.run_sync()
        return {"ok": True, **result}
    except Exception as exc:  # noqa: BLE001 - Ursache an die UI durchreichen
        raise HTTPException(status_code=500, detail=str(exc))
