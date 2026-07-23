"""Episoden-Reihenfolge je Serie: Aired (TV) vs. DVD vs. Absolut.

TheTVDB liefert fuer manche Serien mehrere Nummerierungen. Welche zur
Bibliothek passt, entscheidet die tatsaechliche Folgen-Laufzeit: DVD-Folgen sind
oft doppelt so lang wie Aired-Folgen (z.B. 22 statt 11 Minuten). Die passende
Reihenfolge wird deshalb automatisch anhand des Laufzeit-Medians vorgewaehlt.

Der Nutzer kann die Vorwahl pro Serie ueberstimmen (``media_items.episode_order``:
'aired'|'dvd'|'absolute'; NULL = automatisch). Das Ergebnis steht in
``episode_order_resolved`` und steuert, welche Soll-Struktur completeness/seasons
und die Detail-Ansicht verwenden.

Laeuft nach dem Episoden-Sync und VOR completeness.recompute()/seasons.recompute().
"""
import json
import statistics

from .. import db

ORDERS = ("aired", "dvd", "absolute")


def _rv(row, key):
    """Wert aus sqlite3.Row ODER dict lesen (fehlt -> None)."""
    try:
        return row[key]
    except (KeyError, IndexError):
        return None


def _orders_of(row) -> dict:
    """tvdb_orders (JSON) einer Zeile als Dict; robust gegen leer/kaputt."""
    raw = _rv(row, "tvdb_orders")
    try:
        val = json.loads(raw) if raw else {}
    except (TypeError, ValueError):
        val = {}
    return val if isinstance(val, dict) else {}


def effective_structure(row):
    """(season_counts {staffel: anzahl}, gesamt_episoden) fuer die aufgeloeste
    Reihenfolge.

    Fuer Serien ist TheTVDB die primaere Quelle (tvdb_orders) - auch fuer die
    Aired-Reihenfolge. Das entspricht der Provider-Prioritaet (Serie: TheTVDB
    zuerst) und verhindert, dass bei fehlendem TMDb-Key die Staffelstruktur
    verloren geht. TMDb (tmdb_season_counts/tmdb_episodes) dient nur als Rueckfall,
    wenn TheTVDB fuer die Serie keine Struktur geliefert hat."""
    resolved = _rv(row, "episode_order_resolved") or "aired"
    orders = _orders_of(row)
    chosen = resolved if resolved in orders else ("aired" if "aired" in orders else None)
    if chosen:
        o = orders[chosen]
        sc = {int(s): int(n) for s, n in o.get("season_counts", [])}
        return sc, o.get("episodes")
    raw = _rv(row, "tmdb_season_counts")
    try:
        pairs = json.loads(raw) if raw else []
    except (TypeError, ValueError):
        pairs = []
    sc = {int(s): int(n) for s, n in pairs}
    return sc, _rv(row, "tmdb_episodes")


def _auto_pick(lib_runtime, orders: dict) -> str:
    """Reihenfolge waehlen, deren Median-Laufzeit der Bibliothek am naechsten
    kommt. Ohne verwertbares Signal -> 'aired'. Bei Gleichstand 'aired' bevorzugt."""
    cands = [(k, o.get("runtime")) for k, o in orders.items() if o.get("runtime")]
    if not cands:
        return "aired"
    if lib_runtime is None:
        return "aired" if "aired" in orders else cands[0][0]
    cands.sort(key=lambda kv: (abs(kv[1] - lib_runtime), 0 if kv[0] == "aired" else 1))
    return cands[0][0]


def _lib_runtimes() -> dict:
    """{item_id: [runtime_min, ...]} regulaerer Folgen (Staffel >= 1) mit Laufzeit."""
    out: dict = {}
    for e in db.query(
        "SELECT item_id, runtime_min FROM episodes "
        "WHERE season >= 1 AND runtime_min IS NOT NULL AND runtime_min > 0"
    ):
        out.setdefault(e["item_id"], []).append(e["runtime_min"])
    return out


def recompute() -> int:
    """episode_order_resolved je Serie neu bestimmen (Nutzerwahl schlaegt Auto).
    Gibt die Anzahl aktualisierter Serien zurueck."""
    runtimes = _lib_runtimes()
    updates = []
    for row in db.query(
        "SELECT id, tvdb_orders, episode_order FROM media_items WHERE item_type='Serie'"
    ):
        orders = _orders_of(row)
        pref = row["episode_order"] or "auto"
        if pref != "auto" and pref in orders:
            resolved = pref  # Nutzer hat manuell festgelegt.
        elif orders:
            rts = runtimes.get(row["id"]) or []
            lib_rt = statistics.median(rts) if rts else None
            resolved = _auto_pick(lib_rt, orders)
        else:
            resolved = "aired"
        updates.append((resolved, row["id"]))

    with db.get_conn() as conn:
        conn.executemany(
            "UPDATE media_items SET episode_order_resolved=? WHERE id=?", updates
        )
        conn.commit()
    return len(updates)
