"""Metadaten-Dienste-Verwaltung (Phase 5a) - TMDb/TheTVDB/OMDb/AniDB in der DB.

Analog zu ``sources``: im UI angelegt, in der Tabelle ``metadata_providers``
gespeichert, der API-Key liegt verschluesselt (``crypto``). ``priority`` gibt die
Reihenfolge vor (kleiner = zuerst). In dieser Etappe wird nur TMDb tatsaechlich
zur Anreicherung genutzt; die uebrigen Typen sind vorbereitet (Aufloesungslogik
folgt in 5b).
"""
import json
from datetime import datetime, timezone

from .. import config, db
from . import crypto

# Reihenfolge = Vorschlags-/Anzeigereihenfolge im UI.
KINDS = ("tmdb", "tvdb", "omdb", "anidb")
KIND_LABELS = {"tmdb": "TMDb", "tvdb": "TheTVDB", "omdb": "OMDb", "anidb": "AniDB"}
# Priorisierung erfolgt je Medienart (Phase 5b). 0 = Dienst fuer diesen Typ aus.
MEDIA_TYPES = ("film", "serie", "anime")


def _priorities(row: dict) -> dict:
    """Prioritaet je Medienart. Fehlt ein Typ (5a-Bestand), gilt die alte globale
    ``priority`` als Rueckfall. Ergebnis: {film, serie, anime} -> int."""
    try:
        pr = json.loads(row.get("priorities") or "{}")
    except (ValueError, TypeError):
        pr = {}
    base = row["priority"]
    return {t: int(pr.get(t, base)) for t in MEDIA_TYPES}


# -- Lesen ------------------------------------------------------------------
def _public(row: dict) -> dict:
    """Dienst fuer die UI - ohne Klartext-Key, nur mit has_key-Flag."""
    return {
        "id": row["id"],
        "kind": row["kind"],
        "name": row["name"],
        "has_key": bool(row["api_key"]),
        "enabled": bool(row["enabled"]),
        "priorities": _priorities(row),
    }


def list_providers() -> list:
    return [
        _public(dict(r))
        for r in db.query("SELECT * FROM metadata_providers ORDER BY priority, id")
    ]


def get_provider(provider_id: int) -> dict | None:
    rows = db.query("SELECT * FROM metadata_providers WHERE id=?", (provider_id,))
    return dict(rows[0]) if rows else None


def active_by_kind(kind: str) -> dict | None:
    """Aktiver Dienst eines Typs mit hoechster Prioritaet (kleinste Zahl)."""
    rows = db.query(
        "SELECT * FROM metadata_providers WHERE kind=? AND enabled=1 "
        "ORDER BY priority, id LIMIT 1",
        (kind,),
    )
    return dict(rows[0]) if rows else None


def api_key_for(kind: str) -> str:
    """Entschluesselter API-Key des aktiven Dienstes eines Typs ('' wenn keiner)."""
    row = active_by_kind(kind)
    return crypto.decrypt(row["api_key"] or "") if row else ""


def chain_kinds(media_type: str) -> list:
    """Reihenfolge der Dienst-Typen fuer eine Medienart: nur aktive Dienste mit
    Prioritaet > 0, kleinste Prioritaet zuerst; je Typ nur der beste Eintrag."""
    best = {}
    for r in db.query("SELECT * FROM metadata_providers WHERE enabled=1"):
        prio = _priorities(dict(r)).get(media_type, 0)
        if prio <= 0:
            continue
        if r["kind"] not in best or prio < best[r["kind"]]:
            best[r["kind"]] = prio
    return [k for k, _p in sorted(best.items(), key=lambda kv: kv[1])]


# -- Schreiben --------------------------------------------------------------
def _clean_priorities(priorities) -> dict:
    """Eingabe (dict oder None) -> {film, serie, anime} mit int >= 0. Standard 100."""
    pr = priorities if isinstance(priorities, dict) else {}
    out = {}
    for t in MEDIA_TYPES:
        try:
            out[t] = max(0, int(pr.get(t, 100)))
        except (ValueError, TypeError):
            out[t] = 100
    return out


def create_provider(kind: str, name: str = "", api_key: str = "",
                    enabled: bool = True, priorities=None) -> int:
    if kind not in KINDS:
        raise ValueError(f"Unbekannter Metadaten-Dienst: {kind}")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    pr = _clean_priorities(priorities)
    return db.execute(
        "INSERT INTO metadata_providers(kind, name, api_key, enabled, priority, priorities, created_at) "
        "VALUES(?,?,?,?,?,?,?)",
        (kind, (name or KIND_LABELS.get(kind, kind)).strip(),
         crypto.encrypt(api_key or ""), 1 if enabled else 0,
         min(pr.values()), json.dumps(pr), now),
    )


def update_provider(provider_id: int, name=None, api_key=None,
                   enabled=None, priorities=None) -> None:
    """Felder aktualisieren. ``api_key=None`` (leeres Feld im UI) laesst den Key
    unveraendert; ``priorities=None`` laesst die Prioritaeten unveraendert."""
    row = get_provider(provider_id)
    if not row:
        raise ValueError("Metadaten-Dienst nicht gefunden")
    new_key = row["api_key"] if not api_key else crypto.encrypt(api_key)
    pr = _priorities(row) if priorities is None else _clean_priorities(priorities)
    db.execute(
        "UPDATE metadata_providers SET name=?, api_key=?, enabled=?, priority=?, priorities=? WHERE id=?",
        (
            row["name"] if name is None else name.strip(),
            new_key,
            row["enabled"] if enabled is None else (1 if enabled else 0),
            min(pr.values()), json.dumps(pr),
            provider_id,
        ),
    )


def delete_provider(provider_id: int) -> None:
    db.execute("DELETE FROM metadata_providers WHERE id=?", (provider_id,))


# -- Einmalige Migration env -> DB ------------------------------------------
def ensure_seed_from_env() -> None:
    """TMDb-Key aus der alten ENV-Variable in die DB uebernehmen - genau einmal.

    Nur wenn ``TMDB_API_KEY`` gesetzt ist UND noch kein TMDb-Dienst existiert.
    So laeuft eine bestehende Installation ohne Zutun weiter; die ENV bleibt als
    Fallback in ``tmdb`` erhalten.
    """
    if not config.TMDB_API_KEY:
        return
    if db.query("SELECT 1 FROM metadata_providers WHERE kind='tmdb' LIMIT 1"):
        return
    create_provider("tmdb", name="TMDb", api_key=config.TMDB_API_KEY, enabled=True)
