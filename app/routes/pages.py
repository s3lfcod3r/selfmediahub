"""HTML-Seiten: Uebersicht, Tags, Regeln, Setup."""
import json
import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .. import config, db
from ..services import queries, rules, tags

router = APIRouter()

_TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=_TEMPLATE_DIR)


def _ctx(request: Request, **extra) -> dict:
    base = {"request": request, "app": config}
    base.update(extra)
    return base


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    if not config.any_source_configured():
        return templates.TemplateResponse(request, "setup.html", _ctx(request))
    items = queries.get_items()
    return templates.TemplateResponse(request, "index.html", _ctx(
        request,
        items_json=json.dumps(items, ensure_ascii=False),
        libraries=queries.get_libraries(),
        stats=queries.compute_stats(items),
        last_sync=db.get_meta("last_sync") or "",
        allow_write=config.ALLOW_EMBY_WRITE,
    ))


@router.get("/tags", response_class=HTMLResponse)
def tags_page(request: Request):
    return templates.TemplateResponse(request, "tags.html", _ctx(
        request, tags=tags.list_tags(),
    ))


@router.get("/regeln", response_class=HTMLResponse)
def rules_page(request: Request):
    return templates.TemplateResponse(request, "rules.html", _ctx(
        request, rules=rules.list_rules(), tags=tags.list_tags(),
        fields=rules.FIELDS, ops=rules.OPS,
    ))
