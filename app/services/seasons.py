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


# Wieviele Folgen darf eine Staffel MEHR haben, als der Dienst kennt, ohne dass
# die Aufteilung als abweichend gilt? 1-2 sind der Normalfall: ein Zweiteiler
# zaehlt beim Dienst als EINE Folge, liegt in der Mediathek aber als zwei Dateien.
MAX_EXTRA_PER_SEASON = 2


def _is_reliable(regular_have: dict, tmdb: dict) -> bool:
    """Passt die Staffel-Zuordnung zwischen Quelle und TMDb zusammen?

    Gleiche Heuristik wie ``tmdb.season_summary``: unbekannte Staffeln oder mehr
    Folgen als TMDb kennt heißen, dass die Nummerierung auseinanderläuft.
    """
    if not tmdb:
        return False
    return all(s in tmdb and regular_have[s] <= tmdb[s] for s in regular_have)


def layout_matches(regular_have: dict, tmdb: dict) -> bool:
    """Laesst sich die Aufteilung der Quelle auf die des Dienstes abbilden?

    Toleranter als ``_is_reliable``: ein kleiner Ueberschuss (getrennt abgelegte
    Doppelfolge) ist erlaubt, ebenso Staffeln, von denen noch gar nichts da ist.
    Nicht abbildbar ist es, wenn eine Staffel deutlich mehr Folgen hat als bekannt
    oder wenn wir Folgen in einer Staffel haben, die der Dienst gar nicht kennt -
    dann liegen die Folgen schlicht anders einsortiert (Absolut-Nummerierung,
    eigener Schnitt) und Aussagen JE STAFFEL waeren geraten.
    """
    if not tmdb:
        return False
    for s, h in regular_have.items():
        if h <= 0:
            continue
        t = tmdb.get(s)
        if not t or h - t > MAX_EXTRA_PER_SEASON:
            return False
    return True


def _status_for(have: dict, tmdb: dict) -> list:
    """Staffelliste [{s, st, h, t}] für eine Serie (s = Staffelnummer).

    Bewertung je Staffel EINZELN - eine abweichende Staffel graut nur sich selbst
    aus, nicht die ganze Serie:

    * Staffel kennt der Dienst nicht / wir haben mehr Folgen als er kennt
      -> "unbekannt" (Nummerierung dieser Staffel passt nicht).
    * sonst: vollstaendig (>= Soll), teilweise (1..Soll-1) oder fehlt (0).

    ``strict`` (= passt die GESAMT-Nummerierung, gleiche Pruefung wie
    completeness.recompute) steuert nur eines: ob eine Staffel ohne eine einzige
    Folge als "fehlt" (rot) behauptet werden darf. Ist die Nummerierung insgesamt
    fraglich (z.B. Quelle nutzt Absolut-Nummerierung, alles in Staffel 1), zeigen
    leere Staffeln "unbekannt" statt eines falschen "fehlt".
    """
    regular_have = {s: n for s, n in have.items() if s >= 1}
    strict = _is_reliable(regular_have, tmdb)
    # Liegen die Folgen ueberhaupt so, wie der Dienst die Staffeln schneidet? Wenn
    # nicht (z.B. Naruto: 220 Folgen in 2 Ordnern statt 5 Staffeln), waere jede
    # Ampel geraten - dann ist die ganze Reihe grau. Die Serie bekommt ihr Urteil
    # in dem Fall aus dem Gesamtvergleich (completeness._judge).
    mapped = layout_matches(regular_have, tmdb)

    rows = []
    # Specials nur bei tatsächlich vorhandenen Folgen - und ohne "teilweise".
    if have.get(0):
        rows.append({"s": 0, "st": FULL, "h": have[0], "t": None})

    # Vereinigung aus "kennt der Dienst" und "haben wir".
    for s in sorted(set(tmdb) | set(regular_have)):
        h = regular_have.get(s, 0)
        t = tmdb.get(s)
        if not mapped or not t or h > t:
            st = UNKNOWN
        elif h == 0:
            st = NONE if strict else UNKNOWN
        elif h >= t:
            st = FULL
        else:
            st = PARTIAL
        rows.append({"s": s, "st": st, "h": h, "t": t})
    return rows


def recompute() -> int:
    """season_status je Serie neu berechnen. Gibt die Anzahl Serien zurück."""
    have_map = _have_by_item()
    updates = []
    for row in db.query(
        "SELECT id, tmdb_season_counts, tvdb_orders, episode_order_resolved "
        "FROM media_items WHERE item_type='Serie'"
    ):
        # Soll-Struktur aus der aufgeloesten Reihenfolge (Aired/DVD/Absolut).
        tmdb, _total = episode_order.effective_structure(row)
        rows = _status_for(have_map.get(row["id"], {}), tmdb)
        updates.append((json.dumps(rows) if rows else None, row["id"]))

    with db.get_conn() as conn:
        conn.executemany("UPDATE media_items SET season_status=? WHERE id=?", updates)
        conn.commit()
    return len(updates)
