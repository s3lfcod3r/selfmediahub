"""HTML-Seiten: Uebersicht, Qualitaetskontrolle, Tags, Regeln, Setup."""
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

LOWRES_HEIGHT = 720  # Filme unter dieser Bildhoehe gelten als niedrig aufgeloest


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


@router.get("/qualitaet", response_class=HTMLResponse)
def quality(request: Request):
    items = queries.get_items()
    acked = {(r["source_kind"], r["source_id"])
             for r in db.query("SELECT source_kind, source_id FROM fsk_acks")}

    def is_acked(i):
        return (i["source_kind"], i["source_id"]) in acked

    problems = {
        "no_rating": [i for i in items if not i.get("official_rating") and not is_acked(i)],
        "suspicious": [i for i in items if i.get("fsk_suspicious") and not is_acked(i)],
        "incomplete": [i for i in items if i.get("completeness") == "incomplete"],
        "lowres": [i for i in items if i["item_type"] == "Film"
                   and i.get("height") and i["height"] < LOWRES_HEIGHT],
    }
    return templates.TemplateResponse(request, "quality.html", _ctx(
        request, problems=problems, stats=queries.compute_stats(items),
        allow_write=config.ALLOW_EMBY_WRITE, tmdb=config.tmdb_enabled(),
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
