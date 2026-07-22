"""Metadaten-Dienste (Phase 5c): zwei feste Dienste - TMDb + TheTVDB.

Genau zwei Eintraege, im UI nur ein-/ausschaltbar (Standard AUS) und mit
API-Key (verschluesselt via ``crypto``). Die Anreicherungsreihenfolge ist fest
verdrahtet: Serien/Anime zuerst TheTVDB (bessere Episoden), Filme zuerst TMDb
(Abdeckung + Freigaben). Der jeweils andere Dienst dient als Rueckfall.
"""
from datetime import datetime, timezone

from .. import config, db
from . import crypto

KINDS = ("tmdb", "tvdb")
KIND_LABELS = {"tmdb": "TMDb", "tvdb": "TheTVDB"}
# Feste Reihenfolge je Medienart - nur aktivierte Dienste zaehlen.
FIXED_ORDER = {
    "film": ("tmdb", "tvdb"),
    "serie": ("tvdb", "tmdb"),
    "anime": ("tvdb", "tmdb"),
}

# Eingebaute Projekt-Keys aus der Umgebung (via CI-Secret ins Image gebacken).
# Gelten als Rueckfall, wenn der Nutzer keinen eigenen Key im UI hinterlegt hat.
_ENV_KEYS = {"tmdb": config.TMDB_API_KEY, "tvdb": config.TVDB_API_KEY}


# -- Lesen ------------------------------------------------------------------
def _mask_key(plain: str) -> str:
    """Key maskiert: acht Sternchen + letzte 4 Zeichen - so laesst sich pruefen,
    WELCHER Key gesetzt ist, ohne ihn preiszugeben. Leer -> ''."""
    plain = plain or ""
    if len(plain) <= 4:
        return "*" * len(plain)
    return "*" * 8 + plain[-4:]


def _public(row: dict) -> dict:
    """Dienst fuer die UI - ohne Klartext-Key, aber mit maskiertem Hinweis."""
    return {
        "kind": row["kind"],
        "name": row["name"],
        "has_key": bool(row["api_key"]),
        "key_hint": _mask_key(crypto.decrypt(row["api_key"] or "")) if row["api_key"] else "",
        "enabled": bool(row["enabled"]),
    }


def get_by_kind(kind: str) -> dict | None:
    rows = db.query(
        "SELECT * FROM metadata_providers WHERE kind=? ORDER BY id LIMIT 1", (kind,)
    )
    return dict(rows[0]) if rows else None


def list_providers() -> list:
    """Die zwei festen Dienste in kanonischer Reihenfolge (TMDb, TheTVDB)."""
    out = []
    for kind in KINDS:
        row = get_by_kind(kind)
        if row:
            out.append(_public(row))
    return out


def api_key_for(kind: str) -> str:
    """Effektiver Key des Dienstes: der eigene (aktivierte) Key des Nutzers hat
    Vorrang, sonst der eingebaute Projekt-Key (ENV). '' wenn beides fehlt."""
    row = get_by_kind(kind)
    if row and row["enabled"]:
        key = crypto.decrypt(row["api_key"] or "")
        if key:
            return key
    return _ENV_KEYS.get(kind) or ""


def chain_kinds(media_type: str) -> list:
    """Feste Reihenfolge fuer eine Medienart, gefiltert auf aktivierte Dienste."""
    order = FIXED_ORDER.get(media_type, ("tmdb", "tvdb"))
    enabled = {
        r["kind"] for r in db.query("SELECT kind FROM metadata_providers WHERE enabled=1")
    }
    # Eingebaute Projekt-Keys (ENV) zaehlen ebenfalls als aktiv, damit die
    # Anreicherung ohne UI-Konfiguration funktioniert.
    enabled |= {k for k, v in _ENV_KEYS.items() if v}
    return [k for k in order if k in enabled]


# -- Schreiben --------------------------------------------------------------
def set_provider(kind: str, api_key=None, enabled=None) -> None:
    """Key und/oder Aktiv-Status eines festen Dienstes setzen. ``api_key=None``
    (leeres Feld im UI) laesst den gespeicherten Key unveraendert."""
    if kind not in KINDS:
        raise ValueError(f"Unbekannter Metadaten-Dienst: {kind}")
    row = get_by_kind(kind)
    if not row:
        raise ValueError("Metadaten-Dienst nicht gefunden")
    new_key = row["api_key"] if not api_key else crypto.encrypt(api_key)
    db.execute(
        "UPDATE metadata_providers SET api_key=?, enabled=? WHERE kind=?",
        (new_key, row["enabled"] if enabled is None else (1 if enabled else 0), kind),
    )


def ensure_fixed_providers() -> None:
    """Tabelle auf genau die zwei festen Dienste (je eine Zeile) normalisieren.

    - Fremd-Typen aus der dynamischen 5a/5b-Phase (omdb/anidb) werden entfernt.
    - Mehrfach-Eintraege gleichen Typs (5b erlaubte das) auf die *beste* Zeile
      reduziert (aktiv + Key bevorzugt), der Rest geloescht - so lesen und
      schreiben (get_by_kind/set_provider) garantiert dieselbe Zeile.
    - Fehlende Dienste anlegen: TMDb uebernimmt einen ENV-Key und startet dann
      aktiv (bestehende Installationen brechen nicht), sonst beide leer und AUS.

    Idempotent; laeuft bei jedem Start.
    """
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    db.execute("DELETE FROM metadata_providers WHERE kind NOT IN ('tmdb','tvdb')")
    for kind in KINDS:
        rows = db.query("SELECT * FROM metadata_providers WHERE kind=?", (kind,))
        if not rows:
            key = config.TMDB_API_KEY if kind == "tmdb" else ""
            db.execute(
                "INSERT INTO metadata_providers(kind, name, api_key, enabled, created_at) "
                "VALUES(?,?,?,?,?)",
                (kind, KIND_LABELS[kind], crypto.encrypt(key or ""), 1 if key else 0, now),
            )
        elif len(rows) > 1:
            best = max(rows, key=lambda r: (
                1 if r["enabled"] and r["api_key"] else 0,
                1 if r["enabled"] else 0,
                1 if r["api_key"] else 0,
            ))
            for r in rows:
                if r["id"] != best["id"]:
                    db.execute("DELETE FROM metadata_providers WHERE id=?", (r["id"],))
