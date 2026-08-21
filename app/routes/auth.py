"""Login-, Logout- und Ersteinrichtungs-Seiten (Ein-Konto-Auth)."""
import logging
import os
from urllib.parse import parse_qs

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .. import config, i18n
from ..services import auth, settings as settings_service

router = APIRouter()
logger = logging.getLogger("selfmediahub.auth")


def _peer_ip(request: Request) -> str:
    """Tatsaechliche Gegenstelle der Verbindung - nicht faelschbar."""
    return request.client.host if request.client else "?"


def _client_ip(request: Request) -> str:
    """Client-IP fuer Auth-Logs. Hinter Reverse-Proxy zaehlt der erste
    X-Forwarded-For-Eintrag, sonst die direkte Peer-Adresse."""
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return _peer_ip(request)


def _throttle_key(request: Request) -> str:
    """Schluessel fuer die Anmelde-Bremse.

    Bewusst NICHT ``_client_ip``: X-Forwarded-For setzt der Client selbst, ein
    Angreifer koennte bei jedem Versuch einen anderen Wert schicken und waere nie
    gesperrt. Gezaehlt wird deshalb auf die echte Gegenstelle - und nur dann auf
    den weitergereichten Wert, wenn die Gegenstelle ein als vertrauenswuerdig
    hinterlegter Proxy ist (SMH_TRUSTED_PROXIES).
    """
    peer = _peer_ip(request)
    if peer in config.TRUSTED_PROXIES:
        fwd = request.headers.get("x-forwarded-for")
        if fwd:
            return "fwd:" + fwd.split(",")[0].strip()
    return "peer:" + peer

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


def _secure_cookie(request: Request) -> bool:
    """Darf das Sitzungs-Cookie auf HTTPS beschraenkt werden?

    Mit ``Secure`` schickt der Browser es nur ueber HTTPS - richtig, sobald die
    Instanz hinter einem Reverse Proxy (Zoraxy) haengt. Im LAN laeuft sie aber
    per HTTP; dort wuerde das Flag die Anmeldung unmoeglich machen. Deshalb
    abhaengig vom tatsaechlichen Schema, inklusive der Proxy-Angabe
    X-Forwarded-Proto (der Proxy terminiert TLS und spricht intern HTTP).
    SMH_COOKIE_SECURE=1 erzwingt es unabhaengig davon.

    Der Header ist hier bewusst ungeprueft: Wer ihn faelscht, erzwingt lediglich
    ein strengeres Cookie fuer sich selbst - abschalten laesst sich der Schutz so
    nicht.
    """
    if config.COOKIE_SECURE:
        return True
    fwd = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip().lower()
    return fwd == "https" or request.url.scheme == "https"


def _set_session(resp, username: str, request: Request) -> None:
    resp.set_cookie(
        auth.SESSION_COOKIE, auth.make_session(username),
        max_age=auth._SESSION_MAX_AGE, httponly=True, samesite="lax", path="/",
        secure=_secure_cookie(request),
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
    logger.info("Konto angelegt: user=%s ip=%s", username, _client_ip(request))
    resp = RedirectResponse("/", status_code=303)
    _set_session(resp, username, request)
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
    ip = _client_ip(request)
    key = _throttle_key(request)
    lang = settings_service.get("general.ui_language")

    # Zu viele Fehlversuche von dieser Adresse -> gar nicht erst pruefen.
    wait = auth.login_blocked_for(key)
    if wait:
        logger.warning("Login gesperrt (zu viele Versuche): ip=%s noch %ss", ip, wait)
        minutes = max(1, (wait + 59) // 60)
        return templates.TemplateResponse(
            request, "login.html",
            _ctx(request, lang=lang,
                 error=i18n.t("login.error_locked", lang).replace("{min}", str(minutes))),
            status_code=429, headers={"Retry-After": str(wait)})

    if auth.verify_login(username, pw):
        auth.reset_login_attempts(key)
        logger.info("Login erfolgreich: user=%s ip=%s", username, ip)
        resp = RedirectResponse("/", status_code=303)
        _set_session(resp, username, request)
        return resp
    # Sicherheitsrelevant: fehlgeschlagene Versuche als WARNING (Passwort NIE loggen).
    auth.note_failed_login(key)
    logger.warning("Login fehlgeschlagen: user=%s ip=%s", username or "(leer)", ip)
    return templates.TemplateResponse(
        request, "login.html",
        _ctx(request, lang=lang, error=i18n.t("login.error_bad", lang)), status_code=401)


@router.get("/logout")
def logout(request: Request):
    logger.info("Logout: ip=%s", _client_ip(request))
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie(auth.SESSION_COOKIE, path="/")
    return resp
