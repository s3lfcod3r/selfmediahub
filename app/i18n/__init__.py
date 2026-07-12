"""Einfaches i18n (DE/EN) ohne Zusatz-Abhaengigkeit.

Kataloge sind schlichte Dicts mit namespaced Keys (``nav.overview`` usw.).
Die UI-Sprache ist instanzweit (Single-User-App) und liegt als
``general.ui_language`` in den Einstellungen. Fehlt ein Key, wird der Key-Name
zurueckgegeben - so fallen Luecken beim Testen sofort auf.

Verwendung:
- Templates: ``t`` ist als Kontext-Funktion verfuegbar -> ``{{ t('nav.overview') }}``
- JS: der aktive Katalog wird in ``base.html`` als ``window.__T__`` injiziert.
"""
from .de import STRINGS as _DE
from .en import STRINGS as _EN

DEFAULT_LANG = "de"
CATALOGS = {"de": _DE, "en": _EN}
# (Code, Anzeigename) - Reihenfolge = Reihenfolge in den Dropdowns.
LANGUAGES = [("de", "Deutsch"), ("en", "English")]


def normalize(lang) -> str:
    return lang if lang in CATALOGS else DEFAULT_LANG


def catalog(lang) -> dict:
    return CATALOGS[normalize(lang)]


def t(key: str, lang=None) -> str:
    """Uebersetzung oder - wenn nicht vorhanden - der Key-Name selbst."""
    return catalog(lang).get(key, key)


def context(lang) -> dict:
    """Template-Kontext fuer i18n (t-Funktion, aktive Sprache, Katalog fuer JS)."""
    lang = normalize(lang)
    return {
        "t": lambda key: t(key, lang),
        "ui_lang": lang,
        "ui_languages": LANGUAGES,
        "i18n_catalog": catalog(lang),
    }
