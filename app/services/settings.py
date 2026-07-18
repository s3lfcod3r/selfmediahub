"""Benutzer-Einstellungen: Key-Value-Store in SQLite, Werte als JSON.

Bewusst getrennt von ``app_meta`` (interner Systemzustand wie letzter Scan).
Erweiterbar ohne DB-Migration: eine neue Einstellung = ein neuer Schluessel in
``DEFAULTS``. Fuer listen-artige Konfiguration (mehrere Quellen, Metadienste mit
Reihenfolge) kommen in spaeteren Phasen eigene relationale Tabellen dazu -
dieser Store bleibt fuer einfache/skalare Werte.

Schluessel sind nach Bereich gruppiert: ``<kategorie>.<name>`` (z.B.
``general.instance_name``). Nur in ``DEFAULTS`` bekannte Schluessel werden
gespeichert (siehe ``allowed_keys``) - das dokumentiert alle Einstellungen an
einer Stelle und verhindert das Ablegen beliebiger Fremd-Schluessel.
"""
import json

from .. import db

# Alle bekannten Einstellungen mit ihrem Standardwert. Fehlt ein Schluessel in
# der DB, gilt der Default. Neue Phasen ergaenzen hier ihre Schluessel.
DEFAULTS = {
    # -- Allgemein (Phase 0, funktionsfaehig) --
    "general.instance_name": "",       # optionaler Anzeigename der Instanz (Topbar/Titel)
    "general.ui_language": "de",       # Sprache der Oberflaeche (i18n): de | en
    # -- Anzeige (Phase 2) --
    "display.primary_language": "ger",  # primaere Sprache der Instanz (fuer Sprach-Abdeckung/Flaggen)
    # -- FSK & Altersfreigaben (Phase 1 / 5c) --
    "fsk.enabled": True,               # FSK-Feature an/aus (nur UI - Daten bleiben gespeichert)
    "display.rating_translate": False,  # Freigaben in die bevorzugte Rating-Art umrechnen? (Phase 5d, Fix 3)
    "display.rating_art": "fsk",       # bevorzugte Rating-Art: fsk|usk|pegi|mpaa|ustv|bbfc|age (Phase 5c.2 / 5d Fix 6)
}


def allowed_keys() -> set:
    """Schluessel, die gespeichert werden duerfen (= alle in DEFAULTS)."""
    return set(DEFAULTS)


def _decode(raw):
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return raw


def get(key: str, default=None):
    """Einzelwert lesen (DB -> Default aus DEFAULTS -> uebergebener default)."""
    row = db.query("SELECT value FROM settings WHERE key=?", (key,))
    if row:
        return _decode(row[0]["value"])
    if key in DEFAULTS:
        return DEFAULTS[key]
    return default


def save(key: str, value) -> None:
    """Einzelwert schreiben (unbekannte Schluessel werden ignoriert)."""
    if key not in DEFAULTS:
        return
    db.execute(
        "INSERT INTO settings(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, json.dumps(value)),
    )


def save_many(values: dict) -> None:
    for key, value in values.items():
        save(key, value)


def all_settings() -> dict:
    """Vollstaendige Sicht: Defaults, ueberschrieben von DB-Werten."""
    out = dict(DEFAULTS)
    for row in db.query("SELECT key, value FROM settings"):
        if row["key"] in DEFAULTS:
            out[row["key"]] = _decode(row["value"])
    return out
