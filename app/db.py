"""SQLite-Zugriff. Hält SelfMediaHubs eigene Daten - schreibt nie in Fremdsysteme."""
import json
import os
import sqlite3

from . import config

# Spalten eines media_items in fester Reihenfolge (steuert INSERT/UPDATE).
ITEM_COLUMNS = [
    "source_kind", "source_id", "source_ref", "item_type", "name", "sort_name", "year",
    "official_rating", "community_rating", "genres", "image_url", "library_name",
    "child_count", "overview", "path", "tmdb_id", "imdb_id", "status",
    "tmdb_seasons", "tmdb_episodes", "have_seasons", "have_episodes",
    "completeness", "missing_episodes", "video_codec", "width", "height",
    "resolution", "hdr", "audio_codecs", "audio_langs", "subtitle_langs",
    "runtime_min", "size_bytes", "fsk_suggested", "fsk_suspicious", "fsk_reason",
    "synced_at",
]
JSON_COLUMNS = {"genres", "audio_codecs", "audio_langs", "subtitle_langs"}

# Episoden-Spalten (eigene Tabelle, pro Folge eine Zeile).
EPISODE_COLUMNS = [
    "item_id", "season", "episode", "name", "resolution", "width", "height",
    "video_codec", "hdr", "audio_langs", "subtitle_langs", "size_bytes",
    "runtime_min", "path",
]
EPISODE_JSON = {"audio_langs", "subtitle_langs"}

# Typ je Spalte - für Migration bestehender (v0.1) Datenbanken.
_ITEM_COLDEF = {
    "source_kind": "TEXT", "source_id": "TEXT", "source_ref": "INTEGER", "item_type": "TEXT",
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
    # Abdeckung der primaeren Sprache (Prozent 0-100); per coverage-Service befuellt.
    "primary_audio_pct": "INTEGER", "primary_sub_pct": "INTEGER",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS media_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_kind TEXT NOT NULL,
  source_id   TEXT NOT NULL,
  source_ref  INTEGER,
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
  primary_audio_pct INTEGER, primary_sub_pct INTEGER,
  UNIQUE(source_ref, source_id)
);
CREATE INDEX IF NOT EXISTS idx_items_type ON media_items(item_type);
CREATE INDEX IF NOT EXISTS idx_items_lib  ON media_items(library_name);

-- Episoden je Serie (item_id -> media_items.id). Wird beim Sync neu befuellt.
CREATE TABLE IF NOT EXISTS episodes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id INTEGER NOT NULL,
  season INTEGER, episode INTEGER, name TEXT,
  resolution TEXT, width INTEGER, height INTEGER, video_codec TEXT, hdr TEXT,
  audio_langs TEXT, subtitle_langs TEXT, size_bytes INTEGER, runtime_min INTEGER, path TEXT,
  FOREIGN KEY (item_id) REFERENCES media_items(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_episodes_item ON episodes(item_id);

CREATE TABLE IF NOT EXISTS app_meta (key TEXT PRIMARY KEY, value TEXT);

-- Benutzer-Einstellungen (Key-Value, Wert als JSON). Getrennt von app_meta
-- (interner Systemzustand). Erweiterbar ohne Migration: neuer Schluessel genuegt.
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);

-- Einzelnes Konto (Single-User). Passwort nur als PBKDF2-Hash. id ist immer 1.
CREATE TABLE IF NOT EXISTS account (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  username TEXT NOT NULL,
  pw_hash TEXT NOT NULL,
  email TEXT DEFAULT '',
  auth_enabled INTEGER NOT NULL DEFAULT 1,
  created_at TEXT
);

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
  source_kind TEXT,
  source_id   TEXT NOT NULL,
  source_ref  INTEGER,
  PRIMARY KEY (source_ref, source_id)
);

-- Datenquellen: in der DB statt in ENV-Variablen. Mehrere Quellen je Typ
-- erlaubt (kind NICHT unique) - eindeutig ist die id. `secret` ist der
-- verschluesselte API-Key/Token (crypto-Service). `libraries`/`local_paths`
-- als JSON-Liste; libraries leer = alle Bibliotheken.
CREATE TABLE IF NOT EXISTS sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind        TEXT NOT NULL,
  name        TEXT NOT NULL,
  base_url    TEXT DEFAULT '',
  secret      TEXT DEFAULT '',
  local_paths TEXT DEFAULT '',
  libraries   TEXT DEFAULT '',
  enabled     INTEGER NOT NULL DEFAULT 1,
  created_at  TEXT
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


def _table_sql(conn: sqlite3.Connection, name: str) -> str:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return (row["sql"] if row else "") or ""


def _norm(sql: str) -> str:
    """Whitespace entfernen + Grossschreibung - fuer robuste Schema-Erkennung."""
    return "".join(sql.split()).upper()


def _migrate_columns(conn: sqlite3.Connection) -> None:
    """Fehlende einfache Spalten in einer aelteren media_items-Tabelle nachziehen."""
    have = {r["name"] for r in conn.execute("PRAGMA table_info(media_items)")}
    for col, coltype in _ITEM_COLDEF.items():
        if col not in have:
            conn.execute(f"ALTER TABLE media_items ADD COLUMN {col} {coltype}")


def _rebuild_by_recreate(conn: sqlite3.Connection, table: str) -> None:
    """Tabelle in die neue Form bringen: alt umbenennen, aus SCHEMA neu anlegen,
    gemeinsame Spalten kopieren, alte Tabelle verwerfen. Erfordert
    ``foreign_keys=OFF`` + ``legacy_alter_table=ON`` (sonst werden Referenzen
    anderer Tabellen beim Umbenennen mit angepasst)."""
    old_cols = [r["name"] for r in conn.execute(f"PRAGMA table_info({table})")]
    conn.execute(f"ALTER TABLE {table} RENAME TO {table}_old")
    conn.executescript(SCHEMA)  # legt {table} in neuer Form an (IF NOT EXISTS)
    new_cols = [r["name"] for r in conn.execute(f"PRAGMA table_info({table})")]
    common = ",".join(c for c in old_cols if c in new_cols)
    conn.execute(f"INSERT INTO {table} ({common}) SELECT {common} FROM {table}_old")
    conn.execute(f"DROP TABLE {table}_old")


def _migrate_structural(conn: sqlite3.Connection) -> None:
    """Multi-Instanz-Umstellung: sources.kind nicht mehr UNIQUE; media_items +
    fsk_acks bekommen source_ref und werden ueber (source_ref, source_id)
    eindeutig. Backfill ordnet bestehende Zeilen der Quelle ihres Typs zu."""
    src_old = "UNIQUE" in _norm(_table_sql(conn, "sources"))
    mi_old = "UNIQUE(SOURCE_REF" not in _norm(_table_sql(conn, "media_items"))
    ack_old = "SOURCE_REF" not in _norm(_table_sql(conn, "fsk_acks"))
    if not (src_old or mi_old or ack_old):
        return
    conn.execute("PRAGMA legacy_alter_table=ON")
    for t in ("sources", "media_items", "fsk_acks"):
        conn.execute(f"DROP TABLE IF EXISTS {t}_old")  # evtl. Reste eines Abbruchs
    if src_old:
        _rebuild_by_recreate(conn, "sources")
    if mi_old:
        _rebuild_by_recreate(conn, "media_items")
        conn.execute(
            "UPDATE media_items SET source_ref="
            "(SELECT id FROM sources WHERE sources.kind=media_items.source_kind) "
            "WHERE source_ref IS NULL"
        )
    if ack_old:
        _rebuild_by_recreate(conn, "fsk_acks")
        conn.execute(
            "UPDATE fsk_acks SET source_ref="
            "(SELECT id FROM sources WHERE sources.kind=fsk_acks.source_kind) "
            "WHERE source_ref IS NULL"
        )
    conn.executescript(SCHEMA)  # nach dem Rebuild fehlende Indizes wiederherstellen
    conn.execute("PRAGMA legacy_alter_table=OFF")


def init_db() -> None:
    _ensure_dir()
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.isolation_level = None  # Autocommit - PRAGMAs + strukturelle Migration
    try:
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.executescript(SCHEMA)
        _migrate_columns(conn)
        _migrate_structural(conn)
    finally:
        conn.close()


def query(sql: str, params: tuple = ()) -> list:
    with get_conn() as conn:
        return conn.execute(sql, params).fetchall()


def execute(sql: str, params: tuple = ()):
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid


# -- Items ------------------------------------------------------------------
def _item_values(source_ref: int, source_kind: str, it: dict, synced_at: str) -> tuple:
    out = []
    for col in ITEM_COLUMNS:
        if col == "source_kind":
            out.append(source_kind)
        elif col == "source_ref":
            out.append(source_ref)
        elif col == "synced_at":
            out.append(synced_at)
        elif col in JSON_COLUMNS:
            out.append(json.dumps(it.get(col) or []))
        else:
            out.append(it.get(col))
    return tuple(out)


def upsert_items(source_ref: int, source_kind: str, items: list, synced_at: str) -> dict:
    """Items einer Quelle einspielen (id bleibt stabil -> Tags überleben).

    Schluessel ist ``(source_ref, source_id)`` - so kollidieren gleiche externe
    IDs zweier Server desselben Typs nicht. Gibt {seen, new, removed} zurueck;
    ``new`` ist die Liste neuer source_ids.
    """
    existing = {
        r["source_id"]
        for r in query("SELECT source_id FROM media_items WHERE source_ref=?", (source_ref,))
    }
    cols = ",".join(ITEM_COLUMNS)
    placeholders = ",".join(["?"] * len(ITEM_COLUMNS))
    updates = ",".join(
        f"{c}=excluded.{c}" for c in ITEM_COLUMNS if c not in ("source_ref", "source_id")
    )
    sql = (
        f"INSERT INTO media_items ({cols}) VALUES ({placeholders}) "
        f"ON CONFLICT(source_ref, source_id) DO UPDATE SET {updates}"
    )
    seen, new_ids = set(), []
    with get_conn() as conn:
        for it in items:
            conn.execute(sql, _item_values(source_ref, source_kind, it, synced_at))
            seen.add(it["source_id"])
            if it["source_id"] not in existing:
                new_ids.append(it["source_id"])
        removed = existing - seen
        if removed:
            conn.executemany(
                "DELETE FROM media_items WHERE source_ref=? AND source_id=?",
                [(source_ref, sid) for sid in removed],
            )
        conn.commit()
    return {"seen": len(seen), "new": new_ids, "removed": len(removed)}


# -- Episoden ---------------------------------------------------------------
def replace_episodes(item_id: int, episodes: list) -> None:
    """Alle Episoden einer Serie ersetzen (DELETE + INSERT in einer Transaktion)."""
    with get_conn() as conn:
        conn.execute("DELETE FROM episodes WHERE item_id=?", (item_id,))
        if episodes:
            cols = ",".join(EPISODE_COLUMNS)
            placeholders = ",".join(["?"] * len(EPISODE_COLUMNS))
            rows = []
            for ep in episodes:
                out = []
                for col in EPISODE_COLUMNS:
                    if col == "item_id":
                        out.append(item_id)
                    elif col in EPISODE_JSON:
                        out.append(json.dumps(ep.get(col) or []))
                    else:
                        out.append(ep.get(col))
                rows.append(tuple(out))
            conn.executemany(f"INSERT INTO episodes ({cols}) VALUES ({placeholders})", rows)
        conn.commit()


def get_episodes(item_id: int) -> list:
    rows = query(
        "SELECT * FROM episodes WHERE item_id=? "
        "ORDER BY (season IS NULL), season, (episode IS NULL), episode",
        (item_id,),
    )
    out = []
    for row in rows:
        ep = dict(row)
        for col in EPISODE_JSON:
            ep[col] = json.loads(ep.get(col) or "[]")
        out.append(ep)
    return out


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
