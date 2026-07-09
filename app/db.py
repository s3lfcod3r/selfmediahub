"""SQLite-Zugriff. Hält SelfMediaHubs eigene Daten - schreibt nie in Fremdsysteme."""
import json
import os
import sqlite3

from . import config

# Spalten eines media_items in fester Reihenfolge (steuert INSERT/UPDATE).
ITEM_COLUMNS = [
    "source_kind", "source_id", "item_type", "name", "sort_name", "year",
    "official_rating", "community_rating", "genres", "image_url", "library_name",
    "child_count", "overview", "path", "tmdb_id", "imdb_id", "status",
    "tmdb_seasons", "tmdb_episodes", "have_seasons", "have_episodes",
    "completeness", "missing_episodes", "video_codec", "width", "height",
    "resolution", "hdr", "audio_codecs", "audio_langs", "subtitle_langs",
    "runtime_min", "size_bytes", "fsk_suggested", "fsk_suspicious", "fsk_reason",
    "synced_at",
]
JSON_COLUMNS = {"genres", "audio_codecs", "audio_langs", "subtitle_langs"}

# Typ je Spalte - für Migration bestehender (v0.1) Datenbanken.
_ITEM_COLDEF = {
    "source_kind": "TEXT", "source_id": "TEXT", "item_type": "TEXT",
    "name": "TEXT", "sort_name": "TEXT", "year": "INTEGER",
    "official_rating": "TEXT", "community_rating": "REAL", "genres": "TEXT",
    "image_url": "TEXT", "library_name": "TEXT", "child_count": "INTEGER",
    "overview": "TEXT", "path": "TEXT", "tmdb_id": "TEXT", "imdb_id": "TEXT",
    "status": "TEXT",
    "tmdb_seasons": "INTEGER", "tmdb_episodes": "INTEGER",
    "have_seasons": "INTEGER", "have_episodes": "INTEGER",
    "completeness": "TEXT", "missing_episodes": "INTEGER",
    "video_codec": "TEXT", "width": "INTEGER", "height": "INTEGER",
    "resolution": "TEXT", "hdr": "TEXT", "audio_codecs": "TEXT",
    "audio_langs": "TEXT", "subtitle_langs": "TEXT", "runtime_min": "INTEGER",
    "size_bytes": "INTEGER",
    "fsk_suggested": "TEXT", "fsk_suspicious": "INTEGER", "fsk_reason": "TEXT",
    "synced_at": "TEXT",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS media_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_kind TEXT NOT NULL,
  source_id   TEXT NOT NULL,
  item_type   TEXT NOT NULL,
  name        TEXT NOT NULL,
  sort_name TEXT, year INTEGER, official_rating TEXT, community_rating REAL,
  genres TEXT, image_url TEXT, library_name TEXT, child_count INTEGER, overview TEXT,
  path TEXT,
  tmdb_id TEXT, imdb_id TEXT, status TEXT,
  tmdb_seasons INTEGER, tmdb_episodes INTEGER, have_seasons INTEGER, have_episodes INTEGER,
  completeness TEXT, missing_episodes INTEGER,
  video_codec TEXT, width INTEGER, height INTEGER, resolution TEXT, hdr TEXT,
  audio_codecs TEXT, audio_langs TEXT, subtitle_langs TEXT, runtime_min INTEGER,
  size_bytes INTEGER,
  fsk_suggested TEXT, fsk_suspicious INTEGER, fsk_reason TEXT,
  synced_at TEXT,
  UNIQUE(source_kind, source_id)
);
CREATE INDEX IF NOT EXISTS idx_items_type ON media_items(item_type);
CREATE INDEX IF NOT EXISTS idx_items_lib  ON media_items(library_name);

CREATE TABLE IF NOT EXISTS app_meta (key TEXT PRIMARY KEY, value TEXT);

CREATE TABLE IF NOT EXISTS tags (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  color TEXT DEFAULT '#33a78c',
  icon TEXT DEFAULT '',
  priority INTEGER DEFAULT 100,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS item_tags (
  item_id INTEGER NOT NULL,
  tag_id  INTEGER NOT NULL,
  auto    INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (item_id, tag_id),
  FOREIGN KEY (item_id) REFERENCES media_items(id) ON DELETE CASCADE,
  FOREIGN KEY (tag_id)  REFERENCES tags(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS rules (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1,
  priority INTEGER DEFAULT 100,
  match_type TEXT DEFAULT 'all',
  conditions TEXT, actions TEXT,
  created_at TEXT
);

-- Vom Benutzer als "passt so" bestätigte FSK-Fälle (überlebt Re-Sync).
CREATE TABLE IF NOT EXISTS fsk_acks (
  source_kind TEXT NOT NULL,
  source_id   TEXT NOT NULL,
  PRIMARY KEY (source_kind, source_id)
);
"""


def _ensure_dir() -> None:
    directory = os.path.dirname(config.DB_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)


def get_conn() -> sqlite3.Connection:
    _ensure_dir()
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Fehlende Spalten in einer aelteren media_items-Tabelle nachziehen."""
    have = {r["name"] for r in conn.execute("PRAGMA table_info(media_items)")}
    for col, coltype in _ITEM_COLDEF.items():
        if col not in have:
            conn.execute(f"ALTER TABLE media_items ADD COLUMN {col} {coltype}")


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        _migrate(conn)
        conn.commit()


def query(sql: str, params: tuple = ()) -> list:
    with get_conn() as conn:
        return conn.execute(sql, params).fetchall()


def execute(sql: str, params: tuple = ()):
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid


# -- Items ------------------------------------------------------------------
def _item_values(source_kind: str, it: dict, synced_at: str) -> tuple:
    out = []
    for col in ITEM_COLUMNS:
        if col == "source_kind":
            out.append(source_kind)
        elif col == "synced_at":
            out.append(synced_at)
        elif col in JSON_COLUMNS:
            out.append(json.dumps(it.get(col) or []))
        else:
            out.append(it.get(col))
    return tuple(out)


def upsert_items(source_kind: str, items: list, synced_at: str) -> dict:
    """Items einer Quelle einspielen (id bleibt stabil -> Tags überleben).

    Gibt {seen, new, removed} zurück; ``new`` ist die Liste neuer source_ids.
    """
    existing = {
        r["source_id"]
        for r in query("SELECT source_id FROM media_items WHERE source_kind=?", (source_kind,))
    }
    cols = ",".join(ITEM_COLUMNS)
    placeholders = ",".join(["?"] * len(ITEM_COLUMNS))
    updates = ",".join(
        f"{c}=excluded.{c}" for c in ITEM_COLUMNS if c not in ("source_kind", "source_id")
    )
    sql = (
        f"INSERT INTO media_items ({cols}) VALUES ({placeholders}) "
        f"ON CONFLICT(source_kind, source_id) DO UPDATE SET {updates}"
    )
    seen, new_ids = set(), []
    with get_conn() as conn:
        for it in items:
            conn.execute(sql, _item_values(source_kind, it, synced_at))
            seen.add(it["source_id"])
            if it["source_id"] not in existing:
                new_ids.append(it["source_id"])
        removed = existing - seen
        if removed:
            conn.executemany(
                "DELETE FROM media_items WHERE source_kind=? AND source_id=?",
                [(source_kind, sid) for sid in removed],
            )
        conn.commit()
    return {"seen": len(seen), "new": new_ids, "removed": len(removed)}


# -- Meta -------------------------------------------------------------------
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
