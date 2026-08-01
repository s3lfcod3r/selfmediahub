"""Staffel-Status je Serie für die Cover-Badges (S0, S1, S2 …).

Pro Staffel eine Ampel: vollständig (grün), teilweise (gelb), fehlt (rot) oder
unbekannt (grau). Zwei Sonderfälle:

* **Staffel 0 (Specials)** kennt nur "vorhanden". TMDbs Zählung schließt Specials
  aus (siehe completeness.py), es gibt also gar keine Soll-Zahl, gegen die sich
  "teilweise" bestimmen ließe. Die Staffel erscheint deshalb nur, wenn wirklich
  Specials vorliegen - und dann immer als vollständig.
* **Unklare Nummerierung** (z.B. Anime mit Absolut-Nummerierung): kennt die
  Quelle Staffeln, die TMDb nicht hat, oder hat eine Staffel mehr Folgen als
  TMDb kennt, passt die Zuordnung nicht. Dann sind alle regulären Staffeln
  "unbekannt" - lieber keine Aussage als eine falsche Lücken-Meldung.

Läuft nach dem Episoden-Sync, da erst dann die Einzelfolgen in der DB liegen.
"""
import json

from .. import db
from . import episode_order

# Status-Werte; das Frontend leitet daraus die CSS-Klasse ab (app.js: seasonRow).
FULL, PARTIAL, NONE, UNKNOWN = "full", "partial", "none", "unknown"


def _have_by_item() -> dict:
    """{item_id: {staffel: anzahl_vorhandener_folgen}} - eine Abfrage, kein N+1."""
    out: dict = {}
    for e in db.query(
        "SELECT item_id, season, COUNT(*) AS n FROM episodes GROUP BY item_id, season"
    ):
        if e["season"] is None:
            continue
        out.setdefault(e["item_id"], {})[e["season"]] = e["n"]
    return out


def _is_reliable(regular_have: dict, tmdb: dict) -> bool:
    """Passt die Staffel-Zuordnung zwischen Quelle und TMDb zusammen?

    Gleiche Heuristik wie ``tmdb.season_summary``: unbekannte Staffeln oder mehr
    Folgen als TMDb kennt heißen, dass die Nummerierung auseinanderläuft.
    """
    if not tmdb:
        return False
    return all(s in tmdb and regular_have[s] <= tmdb[s] for s in regular_have)


# completeness-Wert -> Status des Gesamt-Badges (unsichere Nummerierung).
_OVERALL_ST = {"complete": FULL, "incomplete": PARTIAL}


def _status_for(have: dict, tmdb: dict, completeness=None) -> list:
    """Staffelliste für eine Serie.

    Bei verlaesslicher Zuordnung eine Ampel je Staffel [{s, st, h, t}]. Passt die
    Nummerierung der Quelle nicht zur Metadaten-Struktur (oder fehlt sie ganz),
    wird KEINE irrefuehrende Staffel-fuer-Staffel-Ampel gezeigt - die faerbte jede
    Staffel grau und widerspraeche dem Gesamt-"komplett" im Detail. Stattdessen ein
    einzelnes Gesamt-Badge ({overall: True}), das den Vollstaendigkeits-Status der
    ganzen Serie spiegelt. Specials bleiben in beiden Faellen ihr eigenes Badge.
    """
    regular_have = {s: n for s, n in have.items() if s >= 1}
    reliable = _is_reliable(regular_have, tmdb)

    rows = []
    # Specials nur bei tatsächlich vorhandenen Folgen - und ohne "teilweise".
    if have.get(0):
        rows.append({"s": 0, "st": FULL, "h": have[0], "t": None})

    if reliable:
        # Vereinigung aus "kennt der Dienst" und "haben wir": so bekommt auch eine
        # komplett fehlende Staffel ihr rotes Badge.
        for s in sorted(set(tmdb) | set(regular_have)):
            h = regular_have.get(s, 0)
            t = tmdb.get(s)
            if not t:
                st = UNKNOWN
            elif h == 0:
                st = NONE
            elif h >= t:
                st = FULL
            else:
                st = PARTIAL
            rows.append({"s": s, "st": st, "h": h, "t": t})
        return rows

    # Unsichere/fehlende Zuordnung: ein Gesamt-Badge statt grauer Einzel-Badges.
    if regular_have or tmdb:
        rows.append({"s": -1, "overall": True,
                     "st": _OVERALL_ST.get(completeness, UNKNOWN),
                     "h": sum(regular_have.values()),
                     "t": sum(tmdb.values()) if tmdb else None})
    return rows


def recompute() -> int:
    """season_status je Serie neu berechnen. Gibt die Anzahl Serien zurück."""
    have_map = _have_by_item()
    updates = []
    for row in db.query(
        "SELECT id, tmdb_season_counts, tvdb_orders, episode_order_resolved, completeness "
        "FROM media_items WHERE item_type='Serie'"
    ):
        # Soll-Struktur aus der aufgeloesten Reihenfolge (Aired/DVD/Absolut).
        # completeness ist hier bereits frisch (completeness.recompute laeuft im
        # Sync und in der Order-API VOR seasons.recompute) und speist das
        # Gesamt-Badge bei unsicherer Nummerierung.
        tmdb, _total = episode_order.effective_structure(row)
        rows = _status_for(have_map.get(row["id"], {}), tmdb, row["completeness"])
        updates.append((json.dumps(rows) if rows else None, row["id"]))

    with db.get_conn() as conn:
        conn.executemany("UPDATE media_items SET season_status=? WHERE id=?", updates)
        conn.commit()
    return len(updates)
