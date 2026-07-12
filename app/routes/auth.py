"""Login-, Logout- und Ersteinrichtungs-Seiten (Ein-Konto-Auth)."""
import os
from urllib.parse import parse_qs

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .. import config, i18n
from ..services import auth, settings as settings_service

router = APIRouter()

_TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=_TEMPLATE_DIR)


def _ctx(request: Request, lang: str = None, **extra) -> dict:
    lang = lang or settings_service.get("general.ui_language")
    base = {"request": request, "app": config}
    base.update(i18n.context(lang))
    base.update(extra)
    return base


async def _form(request: Request) -> dict:
    """Formular-Body (application/x-www-form-urlencoded) ohne python-multipart parsen."""
    raw = (await request.body()).decode("utf-8")
    return {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}


def _set_session(resp, username: str) -> None:
    resp.set_cookie(
        auth.SESSION_COOKIE, auth.make_session(username),
        max_age=auth._SESSION_MAX_AGE, httponly=True, samesite="lax", path="/",
    )


# -- Ersteinrichtung (Konto anlegen) ----------------------------------------
@router.get("/setup", response_class=HTMLResponse)
def setup_form(request: Request):
    if auth.account_exists():
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request, "setup_account.html", _ctx(request, error=None))


@router.post("/setup")
async def setup_submit(request: Request):
    if auth.account_exists():
        return RedirectResponse("/", status_code=303)
    form = await _form(request)
    username = (form.get("username") or "").strip()
    pw = form.get("password") or ""
    pw2 = form.get("password2") or ""
    email = (form.get("email") or "").strip()
    lang = i18n.normalize(form.get("language") or settings_service.get("general.ui_language"))

    error = None
    if len(username) < 3:
        error = i18n.t("setup.err_username_short", lang)
    elif len(pw) < 8:
        error = i18n.t("setup.err_password_short", lang)
    elif pw != pw2:
        error = i18n.t("setup.err_password_mismatch", lang)
    if error:
        return templates.TemplateResponse(
            request, "setup_account.html",
            _ctx(request, lang=lang, error=error, username=username, email=email), status_code=400)

    auth.create_account(username, pw, email)
    settings_service.save("general.ui_language", lang)
    resp = RedirectResponse("/", status_code=303)
    _set_session(resp, username)
    return resp


# -- Login / Logout ---------------------------------------------------------
@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    if not auth.account_exists():
        return RedirectResponse("/setup", status_code=303)
    return templates.TemplateResponse(request, "login.html", _ctx(request, error=None))


@router.post("/login")
async def login_submit(request: Request):
    form = await _form(request)
    username = (form.get("username") or "").strip()
    pw = form.get("password") or ""
    if auth.verify_login(username, pw):
        resp = RedirectResponse("/", status_code=303)
        _set_session(resp, username)
        return resp
    lang = settings_service.get("general.ui_language")
    return templates.TemplateResponse(
        request, "login.html",
        _ctx(request, lang=lang, error=i18n.t("login.error_bad", lang)), status_code=401)


@router.get("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie(auth.SESSION_COOKIE, path="/")
    return resp
