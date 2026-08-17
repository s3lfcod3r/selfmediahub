"""Vollständigkeit je Serie: vorhandene vs. veröffentlichte Episoden (TMDb).

Wichtig: Beide Seiten zählen **nur reguläre Staffeln (>= 1)**. Staffel 0
(Specials) wird ausgeschlossen, weil TMDbs ``number_of_episodes`` die Specials
ebenfalls nicht mitzählt - sonst wäre die HABEN-Seite künstlich aufgebläht und
unvollständige Serien würden fälschlich als "vollständig" gelten.

Wird nach dem Episoden-Sync aufgerufen (die Einzelfolgen liegen dann in der DB).
"""
from .. import db
from . import episode_order, seasons


def _judge(per_season: dict, sc: dict, total):
    """(completeness, missing) - zweistufig, damit immer eine Aussage herauskommt,
    aber nie eine erfundene Zahl.

    **Stufe 1 (genau), wenn sich die Aufteilung abbilden laesst:** Bewertung je
    Staffel aus denselben Ampeln, die auf dem Cover stehen. Das ist noetig, weil
    die Gesamtzahl Luecken mit Ueberschuss verrechnet - bei Lost hob die Extra-Folge
    in S1 die fehlende in S6 auf, die Serie galt faelschlich als vollstaendig. Eine
    Staffel, von der wir nichts haben und deren Soll-Zahl fehlt, bleibt ein blinder
    Fleck -> Stufe 2.

    **Stufe 2 (grob), wenn die Aufteilung nicht passt:** Dann liegen die Folgen nur
    anders einsortiert (Naruto: 220 Folgen in 2 Ordnern statt 5 Staffeln) - je
    Staffel waere jede Zahl geraten. Verglichen wird die Gesamtzahl der gewaehlten
    Reihenfolge: so viele Folgen kennt der Dienst, so viele sind da. Fuer Naruto
    ergibt das 220 von 220 = vollstaendig, statt frueher "unbekannt" oder gar einer
    Lueckenmeldung. Das Detail-Fenster weist auf die abweichende Nummerierung hin.

    "unbekannt" bleibt damit dem einzigen Fall vorbehalten, in dem wirklich nichts
    bekannt ist: keine Soll-Struktur vom Metadatendienst.
    """
    if not sc:
        return "unknown", None
    regular_have = {s: n for s, n in per_season.items() if s >= 1}
    if seasons.layout_matches(regular_have, sc):
        regular = [r for r in seasons._status_for(per_season, sc) if r["s"] >= 1]
        gaps = sum(max(0, (r["t"] or 0) - r["h"])
                   for r in regular if r["st"] in (seasons.PARTIAL, seasons.NONE))
        if gaps:
            return "incomplete", gaps
        blind = any(r["st"] == seasons.UNKNOWN and r["h"] == 0 for r in regular)
        if not blind and any(r["st"] == seasons.FULL for r in regular):
            return "complete", 0
    # Stufe 2: nur noch die Gesamtzahl ist belastbar.
    if not total:
        return "unknown", None
    missing = max(0, total - sum(regular_have.values()))
    return ("incomplete", missing) if missing else ("complete", 0)


def recompute() -> int:
    """completeness ('complete'|'incomplete'|'unknown') + missing_episodes je Serie.

    HABEN-Seite = gespeicherte Episoden mit ``season >= 1`` (ohne Specials). Sind
    für eine Serie noch keine Episoden gespeichert, greift als Rückfall das
    Emby-Aggregat ``have_episodes``. Gibt die Anzahl aktualisierter Serien zurück.

    Eine "komplett"/"unvollstaendig"-Aussage gibt es nur, wenn sich die
    Nummerierung der Quelle auf die Metadaten-Struktur abbilden laesst (gleiche
    Pruefung wie die Cover-Badges, ``seasons._is_reliable``). Passt sie nicht - z.B.
    Emby teilt anders auf, als TheTVDB es kennt -, bleibt es "unbekannt", statt aus
    einer nicht zuordenbaren Gesamtzahl "komplett" zu behaupten. Fuer Serien ist
    TheTVDB die Soll-Quelle; ein abweichendes ``tmdb_episodes`` bleibt aussen vor.
    """
    # Alle Episoden einmal laden (kein N+1): je Serie die Folgen je Staffel
    # zaehlen (inkl. Staffel 0, die _status_for selbst aussortiert) und merken,
    # welche Serien ueberhaupt Episoden haben.
    have_by_season: dict = {}
    has_episodes: set = set()
    for e in db.query("SELECT item_id, season FROM episodes"):
        has_episodes.add(e["item_id"])
        s = e["season"] or 0
        have_by_season.setdefault(e["item_id"], {})[s] = \
            have_by_season.get(e["item_id"], {}).get(s, 0) + 1

    updates = []
    for row in db.query(
        "SELECT id, tmdb_episodes, have_episodes, tmdb_season_counts, tvdb_orders, "
        "episode_order_resolved FROM media_items WHERE item_type='Serie'"
    ):
        per_season = have_by_season.get(row["id"], {})
        # Soll-Struktur + Gesamtzahl aus der aufgeloesten Reihenfolge.
        sc, total = episode_order.effective_structure(row)

        if row["id"] in has_episodes:
            have = sum(n for s, n in per_season.items() if s >= 1)  # ohne Specials
            completeness, missing = _judge(per_season, sc, total)
        else:
            # Noch keine Einzelfolgen gespeichert -> es gibt nichts, was sich je
            # Staffel pruefen liesse. Dann wie bisher grob gegen die Gesamtzahl.
            have = row["have_episodes"]
            if total and have is not None:
                missing = max(0, total - have)
                completeness = "complete" if missing == 0 else "incomplete"
            else:
                missing, completeness = None, "unknown"
        updates.append((completeness, missing, have, row["id"]))

    with db.get_conn() as conn:
        conn.executemany(
            "UPDATE media_items SET completeness=?, missing_episodes=?, have_episodes=? WHERE id=?",
            updates,
        )
        conn.commit()
    return len(updates)
