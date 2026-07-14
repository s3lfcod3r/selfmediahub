"""Metadaten-Dienste-Verwaltung (Phase 5a) - TMDb/TheTVDB/OMDb/AniDB in der DB.

Analog zu ``sources``: im UI angelegt, in der Tabelle ``metadata_providers``
gespeichert, der API-Key liegt verschluesselt (``crypto``). ``priority`` gibt die
Reihenfolge vor (kleiner = zuerst). In dieser Etappe wird nur TMDb tatsaechlich
zur Anreicherung genutzt; die uebrigen Typen sind vorbereitet (Aufloesungslogik
folgt in 5b).
"""
from datetime import datetime, timezone

from .. import config, db
from . import crypto

# Reihenfolge = Vorschlags-/Anzeigereihenfolge im UI.
KINDS = ("tmdb", "tvdb", "omdb", "anidb")
KIND_LABELS = {"tmdb": "TMDb", "tvdb": "TheTVDB", "omdb": "OMDb", "anidb": "AniDB"}


# -- Lesen ------------------------------------------------------------------
def _public(row: dict) -> dict:
    """Dienst fuer die UI - ohne Klartext-Key, nur mit has_key-Flag."""
    return {
        "id": row["id"],
        "kind": row["kind"],
        "name": row["name"],
        "has_key": bool(row["api_key"]),
        "enabled": bool(row["enabled"]),
        "priority": row["priority"],
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


# -- Schreiben --------------------------------------------------------------
def create_provider(kind: str, name: str = "", api_key: str = "",
                    enabled: bool = True, priority: int = 100) -> int:
    if kind not in KINDS:
        raise ValueError(f"Unbekannter Metadaten-Dienst: {kind}")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return db.execute(
        "INSERT INTO metadata_providers(kind, name, api_key, enabled, priority, created_at) "
        "VALUES(?,?,?,?,?,?)",
        (kind, (name or KIND_LABELS.get(kind, kind)).strip(),
         crypto.encrypt(api_key or ""), 1 if enabled else 0, int(priority), now),
    )


def update_provider(provider_id: int, name=None, api_key=None,
                   enabled=None, priority=None) -> None:
    """Felder aktualisieren. ``api_key=None`` (leeres Feld im UI) laesst den Key
    unveraendert; ein nicht-leerer Wert ersetzt ihn."""
    row = get_provider(provider_id)
    if not row:
        raise ValueError("Metadaten-Dienst nicht gefunden")
    new_key = row["api_key"] if not api_key else crypto.encrypt(api_key)
    db.execute(
        "UPDATE metadata_providers SET name=?, api_key=?, enabled=?, priority=? WHERE id=?",
        (
            row["name"] if name is None else name.strip(),
            new_key,
            row["enabled"] if enabled is None else (1 if enabled else 0),
            row["priority"] if priority is None else int(priority),
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
    create_provider("tmdb", name="TMDb", api_key=config.TMDB_API_KEY,
                    enabled=True, priority=100)
