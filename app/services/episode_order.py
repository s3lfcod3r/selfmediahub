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
    wenn TheTVDB fuer die Serie keine Struktur geliefert hat.

    Ohne Staffelstruktur (leeres ``season_counts``) wird die Gesamtzahl bewusst
    als ``None`` gemeldet, auch wenn ein blankes ``tmdb_episodes`` aus einem
    frueheren Sync herumliegt: sonst wuerde completeness aus einer nicht
    aufschluesselbaren Zahl "komplett" behaupten, waehrend das Cover mangels
    Struktur alle Staffeln ausgraut - genau der Widerspruch, den es zu vermeiden
    gilt."""
    resolved = _rv(row, "episode_order_resolved") or "aired"
    orders = _orders_of(row)
    chosen = resolved if resolved in orders else ("aired" if "aired" in orders else None)
    if chosen:
        o = orders[chosen]
        sc = {int(s): int(n) for s, n in o.get("season_counts", [])}
        return sc, (o.get("episodes") if sc else None)
    raw = _rv(row, "tmdb_season_counts")
    try:
        pairs = json.loads(raw) if raw else []
    except (TypeError, ValueError):
        pairs = []
    sc = {int(s): int(n) for s, n in pairs}
    return sc, (_rv(row, "tmdb_episodes") if sc else None)


def upcoming_of(row) -> list:
    """[[staffel, 'YYYY-MM-DD'], ...] der noch nicht veroeffentlichten Staffeln der
    aufgeloesten Reihenfolge. Leer, wenn keine geplant sind oder keine TheTVDB-
    Struktur vorliegt (TMDb-Rueckfall kennt diese Info nicht)."""
    resolved = _rv(row, "episode_order_resolved") or "aired"
    orders = _orders_of(row)
    chosen = resolved if resolved in orders else ("aired" if "aired" in orders else None)
    if not chosen:
        return []
    up = orders[chosen].get("upcoming") or []
    out = []
    for pair in up:
        try:
            out.append([int(pair[0]), pair[1]])
        except (TypeError, ValueError, IndexError):
            continue
    return out


def _conflict(have: dict, order: dict) -> int:
    """Wie viele Folgen passen NICHT in die Staffelstruktur dieser Reihenfolge?

    Gezaehlt wird nur, was der Struktur widerspricht:

    * Folgen in einer Staffel, die diese Reihenfolge gar nicht kennt (z.B. die
      DVD-Nummerierung der Simpsons endet bei Staffel 32, die Bibliothek hat 37).
    * Folgen ueber der Soll-Zahl einer Staffel (Absolut-Nummerierung: 203 Folgen
      in Staffel 1, wo die Aired-Reihenfolge 35 erwartet).

    FEHLENDE Folgen (weniger als Soll) zaehlen bewusst nicht: das sind echte
    Luecken und kein Hinweis auf die falsche Nummerierung. Wuerde man sie
    mitzaehlen, gewaenne immer die Reihenfolge mit den wenigsten Folgen.
    """
    sc = {int(s): int(n) for s, n in (order.get("season_counts") or [])}
    total = 0
    for season, h in have.items():
        if h <= 0:
            continue
        t = sc.get(season)
        total += h if not t else max(0, h - t)
    return total


def _auto_pick(lib_runtime, orders: dict, have: dict = None) -> str:
    """Passende Reihenfolge waehlen.

    Erstes Kriterium ist die tatsaechliche Staffelaufteilung der Bibliothek
    (``_conflict``) - sie entscheidet, ob sich Vollstaendigkeit spaeter je Staffel
    bestimmen laesst oder nur noch grob ueber die Gesamtzahl. Erst bei Gleichstand
    zaehlt wie bisher die Median-Laufzeit (DVD-Folgen sind oft doppelt so lang wie
    Aired-Folgen), zuletzt hat 'aired' Vorrang. Ohne gespeicherte Folgen bleibt es
    beim reinen Laufzeit-Vergleich.
    """
    if not orders:
        return "aired"
    def sort_key(k):
        conflict = _conflict(have, orders[k]) if have else 0
        rt = orders[k].get("runtime")
        rt_diff = abs(rt - lib_runtime) if (rt and lib_runtime is not None) else 10 ** 6
        return (conflict, rt_diff, 0 if k == "aired" else 1, k)
    return sorted(orders, key=sort_key)[0]


def _lib_runtimes() -> dict:
    """{item_id: [runtime_min, ...]} regulaerer Folgen (Staffel >= 1) mit Laufzeit."""
    out: dict = {}
    for e in db.query(
        "SELECT item_id, runtime_min FROM episodes "
        "WHERE season >= 1 AND runtime_min IS NOT NULL AND runtime_min > 0"
    ):
        out.setdefault(e["item_id"], []).append(e["runtime_min"])
    return out


def _have_by_season() -> dict:
    """{item_id: {staffel: anzahl}} regulaerer Folgen - Basis fuer _conflict."""
    out: dict = {}
    for e in db.query(
        "SELECT item_id, season, COUNT(*) AS n FROM episodes "
        "WHERE season >= 1 GROUP BY item_id, season"
    ):
        out.setdefault(e["item_id"], {})[e["season"]] = e["n"]
    return out


def recompute() -> int:
    """episode_order_resolved je Serie neu bestimmen (Nutzerwahl schlaegt Auto).
    Gibt die Anzahl aktualisierter Serien zurueck."""
    runtimes = _lib_runtimes()
    have_map = _have_by_season()
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
            resolved = _auto_pick(lib_rt, orders, have_map.get(row["id"]))
        else:
            resolved = "aired"
        updates.append((resolved, row["id"]))

    with db.get_conn() as conn:
        conn.executemany(
            "UPDATE media_items SET episode_order_resolved=? WHERE id=?", updates
        )
        conn.commit()
    return len(updates)
