"""HTML-Seiten: Übersicht, Tags, Regeln, Setup."""
import json
import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .. import config, db, i18n
from ..services import (
    auth, queries, rules, settings as settings_service, sources, tags, updatecheck,
)

router = APIRouter()

_TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=_TEMPLATE_DIR)


def _script_json(data) -> str:
    """JSON fuer die Einbettung in einen <script>-Block.

    ``json.dumps`` escaped ``<`` und ``>`` NICHT. Ein Medientitel, Ordnername
    oder Tag, der ``</script>`` enthaelt, wuerde den Script-Block vorzeitig
    beenden - alles Dahinter parst der Browser als HTML und fuehrt es aus
    (Stored XSS ueber den Medienbestand, z.B. ueber einen praeparierten
    Dateinamen). Die drei kritischen Zeichen werden deshalb als Unicode-Escape
    geschrieben: fuer JSON identisch, fuer den HTML-Parser harmlos.
    """
    return (json.dumps(data, ensure_ascii=False)
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("&", "\\u0026"))


def _ctx(request: Request, **extra) -> dict:
    all_settings = settings_service.all_settings()
    base = {
        "request": request, "app": config,
        "settings": all_settings,
        "update": updatecheck.get_status(),
        "account": auth.get_account(),
        "auth_active": auth.auth_active(),
    }
    base.update(i18n.context(all_settings.get("general.ui_language")))
    base.update(extra)
    return base


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    if not sources.any_enabled():
        return templates.TemplateResponse(request, "setup.html", _ctx(request))
    items = queries.get_items()
    return templates.TemplateResponse(request, "index.html", _ctx(
        request,
        items_json=_script_json(items),
        libraries=queries.get_libraries(),
        stats=queries.compute_stats(items),
        last_sync=db.get_meta("last_sync") or "",
        allow_write=config.ALLOW_EMBY_WRITE,
    ))


@router.get("/fsk", response_class=HTMLResponse)
def fsk_page(request: Request):
    # Nur erreichbar, wenn das FSK-Feature aktiv ist.
    if not settings_service.get("fsk.enabled"):
        return RedirectResponse("/", status_code=303)
    items = queries.get_items()
    return templates.TemplateResponse(request, "fsk.html", _ctx(
        request,
        items_json=_script_json(items),
        rating_art=settings_service.get("display.rating_art", "fsk"),
        rating_translate=bool(settings_service.get("display.rating_translate", False)),
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


@router.get("/einstellungen", response_class=HTMLResponse)
def settings_page(request: Request):
    return templates.TemplateResponse(request, "settings.html", _ctx(request))
