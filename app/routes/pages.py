"""HTML-Seiten: Setup-Hinweis oder die Haupt-Uebersicht (Cover + Liste)."""
import json
import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .. import config, db
from ..services import queries

router = APIRouter()

_TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=_TEMPLATE_DIR)


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    if not config.any_source_configured():
        return templates.TemplateResponse(request, "setup.html", {"app": config})

    items = queries.get_items()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "app": config,
            "items_json": json.dumps(items, ensure_ascii=False),
            "libraries": queries.get_libraries(),
            "stats": queries.compute_stats(items),
            "last_sync": db.get_meta("last_sync") or "",
        },
    )
