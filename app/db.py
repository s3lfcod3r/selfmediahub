"""SQLite-Zugriff. Haelt SelfMediaHubs eigene Daten - schreibt nie in Fremdsysteme."""
import json
import os
import sqlite3

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS media_items (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  source_kind      TEXT NOT NULL,
  source_id        TEXT NOT NULL,
  item_type        TEXT NOT NULL,
  name             TEXT NOT NULL,
  sort_name        TEXT,
  year             INTEGER,
  official_rating  TEXT,
  community_rating REAL,
  genres           TEXT,
  image_url        TEXT,
  library_name     TEXT,
  child_count      INTEGER,
  overview         TEXT,
  synced_at        TEXT,
  UNIQUE(source_kind, source_id)
);
CREATE INDEX IF NOT EXISTS idx_items_type ON media_items(item_type);
CREATE INDEX IF NOT EXISTS idx_items_lib  ON media_items(library_name);

CREATE TABLE IF NOT EXISTS app_meta (
  key   TEXT PRIMARY KEY,
  value TEXT
);
"""

_INSERT_COLS = (
    "source_kind, source_id, item_type, name, sort_name, year, "
    "official_rating, community_rating, genres, image_url, "
    "library_name, child_count, overview, synced_at"
)


def _ensure_dir() -> None:
    directory = os.path.dirname(config.DB_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)


def get_conn() -> sqlite3.Connection:
    _ensure_dir()
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def query(sql: str, params: tuple = ()) -> list:
    with get_conn() as conn:
        return conn.execute(sql, params).fetchall()


def replace_source_items(source_kind: str, items: list, synced_at: str) -> None:
    """Alle Items einer Quelle atomar ersetzen (voller Re-Sync)."""
    rows = [
        (
            source_kind,
            it["source_id"],
            it["item_type"],
            it["name"],
            it.get("sort_name"),
            it.get("year"),
            it.get("official_rating"),
            it.get("community_rating"),
            json.dumps(it.get("genres") or []),
            it.get("image_url"),
            it.get("library_name"),
            it.get("child_count"),
            it.get("overview"),
            synced_at,
        )
        for it in items
    ]
    placeholders = ",".join(["?"] * 14)
    with get_conn() as conn:
        conn.execute("DELETE FROM media_items WHERE source_kind=?", (source_kind,))
        conn.executemany(
            f"INSERT INTO media_items ({_INSERT_COLS}) VALUES ({placeholders})",
            rows,
        )
        conn.commit()


def set_meta(key: str, value: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO app_meta(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        conn.commit()


def get_meta(key: str, default=None):
    row = query("SELECT value FROM app_meta WHERE key=?", (key,))
    return row[0]["value"] if row else default
