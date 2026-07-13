"""Datenquellen-Verwaltung (Phase 4a) - Quellen in der DB statt in ENV.

Quellen werden im UI angelegt und in der Tabelle ``sources`` gespeichert;
Zugangsdaten liegen verschluesselt (``crypto``). 4a: genau eine Quelle je Typ
(``kind`` ist UNIQUE). Der ``kind``-String bleibt der Bezug zu
``media_items.source_kind`` - so bleibt der Rest der Pipeline unveraendert.
"""
import json
from datetime import datetime, timezone

from .. import db
from ..connectors.emby import EmbyConnector
from ..connectors.jellyfin import JellyfinConnector
from ..connectors.local import LocalConnector
from ..connectors.plex import PlexConnector
from . import crypto

KINDS = ("emby", "jellyfin", "plex", "local")
# Typen, die eine URL + ein Secret brauchen (local nicht).
SERVER_KINDS = ("emby", "jellyfin", "plex")


def _json_list(raw) -> list:
    try:
        val = json.loads(raw) if raw else []
        return val if isinstance(val, list) else []
    except (ValueError, TypeError):
        return []


# -- Lesen ------------------------------------------------------------------
def _public(row: dict) -> dict:
    """Quelle fuer die UI - ohne Klartext-Secret, nur mit has_secret-Flag."""
    return {
        "id": row["id"],
        "kind": row["kind"],
        "name": row["name"],
        "base_url": row["base_url"] or "",
        "has_secret": bool(row["secret"]),
        "local_paths": _json_list(row["local_paths"]),
        "libraries": _json_list(row["libraries"]),
        "enabled": bool(row["enabled"]),
    }


def list_sources() -> list:
    return [_public(dict(r)) for r in db.query("SELECT * FROM sources ORDER BY kind")]


def get_source(source_id: int) -> dict | None:
    rows = db.query("SELECT * FROM sources WHERE id=?", (source_id,))
    return dict(rows[0]) if rows else None


def get_by_kind(kind: str) -> dict | None:
    rows = db.query("SELECT * FROM sources WHERE kind=?", (kind,))
    return dict(rows[0]) if rows else None


def any_enabled() -> bool:
    return bool(db.query("SELECT 1 FROM sources WHERE enabled=1 LIMIT 1"))


def emby_enabled() -> bool:
    return bool(db.query("SELECT 1 FROM sources WHERE kind='emby' AND enabled=1 LIMIT 1"))


# -- Schreiben --------------------------------------------------------------
def create_source(kind: str, name: str = "", base_url: str = "", secret: str = "",
                   local_paths=None, libraries=None, enabled: bool = True) -> int:
    if kind not in KINDS:
        raise ValueError(f"Unbekannter Quellentyp: {kind}")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return db.execute(
        "INSERT INTO sources(kind, name, base_url, secret, local_paths, libraries, enabled, created_at) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (kind, (name or kind).strip(), (base_url or "").rstrip("/"),
         crypto.encrypt(secret or ""), json.dumps(local_paths or []),
         json.dumps(libraries or []), 1 if enabled else 0, now),
    )


def update_source(source_id: int, name=None, base_url=None, secret=None,
                  local_paths=None, libraries=None, enabled=None) -> None:
    """Felder aktualisieren. ``secret=None`` laesst das Secret unveraendert
    (leeres Feld im UI = Key behalten); ein nicht-leerer Wert ersetzt es."""
    row = get_source(source_id)
    if not row:
        raise ValueError("Quelle nicht gefunden")
    new_secret = row["secret"] if not secret else crypto.encrypt(secret)
    db.execute(
        "UPDATE sources SET name=?, base_url=?, secret=?, local_paths=?, libraries=?, enabled=? WHERE id=?",
        (
            row["name"] if name is None else name.strip(),
            row["base_url"] if base_url is None else base_url.rstrip("/"),
            new_secret,
            row["local_paths"] if local_paths is None else json.dumps(local_paths),
            row["libraries"] if libraries is None else json.dumps(libraries),
            row["enabled"] if enabled is None else (1 if enabled else 0),
            source_id,
        ),
    )


def delete_source(source_id: int) -> None:
    db.execute("DELETE FROM sources WHERE id=?", (source_id,))


# -- Connector-Bau ----------------------------------------------------------
def _connector_from_row(row: dict):
    kind = row["kind"]
    secret = crypto.decrypt(row["secret"] or "")
    libs = _json_list(row["libraries"]) or None
    if kind == "emby":
        conn = EmbyConnector(row["base_url"], secret, libraries=libs)
    elif kind == "jellyfin":
        conn = JellyfinConnector(row["base_url"], secret, libraries=libs)
    elif kind == "plex":
        conn = PlexConnector(row["base_url"], secret, libraries=libs)
    elif kind == "local":
        conn = LocalConnector(_json_list(row["local_paths"]))
    else:
        return None
    # Konkrete Instanz am Connector vermerken (Multi-Instanz: eindeutig ueber id).
    conn.source_ref = row["id"]
    conn.source_name = row["name"]
    return conn


def build_connectors() -> list:
    """Alle aktiven Quellen als Connectoren (fuer den Sync)."""
    conns = []
    for r in db.query("SELECT * FROM sources WHERE enabled=1 ORDER BY kind"):
        conn = _connector_from_row(dict(r))
        if conn:
            conns.append(conn)
    return conns


def connector_for(kind: str):
    """Einzelnen Connector einer aktiven Quelle bauen (z.B. Detail-Abrufe)."""
    row = get_by_kind(kind)
    if not row or not row["enabled"]:
        return None
    return _connector_from_row(row)


def emby_connector():
    """Emby-Connector der gespeicherten Quelle (fuer FSK-Rueckschreiben)."""
    return connector_for("emby")


# -- Test & Bibliotheken (fuer das UI) --------------------------------------
def test_connection(source_id: int) -> None:
    """Verbindung der gespeicherten Quelle pruefen. Wirft bei Fehler."""
    row = get_source(source_id)
    if not row:
        raise ValueError("Quelle nicht gefunden")
    conn = _connector_from_row(row)
    if not conn:
        raise ValueError("Kein Connector fuer diesen Typ")
    conn.test_connection()


def list_libraries(source_id: int) -> list:
    """Verfuegbare Bibliotheken der Quelle auflisten (fuer die Auswahl)."""
    row = get_source(source_id)
    if not row:
        raise ValueError("Quelle nicht gefunden")
    conn = _connector_from_row(row)
    if conn and hasattr(conn, "list_libraries"):
        return conn.list_libraries()
    return []
