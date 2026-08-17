"""Vollständigkeit je Serie: vorhandene vs. veröffentlichte Episoden (TMDb).

Wichtig: Beide Seiten zählen **nur reguläre Staffeln (>= 1)**. Staffel 0
(Specials) wird ausgeschlossen, weil TMDbs ``number_of_episodes`` die Specials
ebenfalls nicht mitzählt - sonst wäre die HABEN-Seite künstlich aufgebläht und
unvollständige Serien würden fälschlich als "vollständig" gelten.

Wird nach dem Episoden-Sync aufgerufen (die Einzelfolgen liegen dann in der DB).
"""
from .. import db
from . import episode_order, seasons


# Wieviele Folgen darf eine Staffel MEHR haben, als der Dienst kennt, ohne dass
# die Zuordnung als kaputt gilt? 1-2 sind der Normalfall: ein Zweiteiler zaehlt
# beim Dienst als EINE Folge, liegt in der Mediathek aber als zwei Dateien. Alles
# darueber heisst, dass die Staffeln anders geschnitten sind (Absolut-Nummerierung,
# eigene Aufteilung) - dann ist jede Lueckenzahl geraten.
MAX_EXTRA_PER_SEASON = 2


def _judge(per_season: dict, sc: dict):
    """(completeness, missing) aus den Staffel-Ampeln - genau denen, die auch auf
    dem Cover stehen (``seasons._status_for``).

    Bewusst je Staffel statt aus der Gesamtzahl. Frueher genuegte EINE Staffel mit
    abweichender Nummerierung, damit die ganze Serie "unbekannt" wurde - auch wenn
    die uebrigen 36 Staffeln sauber zuzuordnen waren und das Cover laengst konkrete
    Luecken zeigte (Emby fuehrt in Simpsons S20 eine Folge mehr, als TheTVDB kennt).
    Umgekehrt verrechnete die Gesamtzahl Luecken mit Ueberschuss: bei Lost hob die
    Extra-Folge in S1 die fehlende in S6 auf -> faelschlich "vollstaendig". Regeln:

    * Staffel mit deutlich mehr Folgen als erwartet (> ``MAX_EXTRA_PER_SEASON``)
      -> "unbekannt". Die Aufteilung passt nicht, jede Lueckenzahl waere geraten.
    * Nachweisbare Luecken (Staffeln gelb/rot) -> "unvollstaendig", ``missing`` =
      Summe genau dieser Luecken.
    * Blinder Fleck = Staffel, von der wir KEINE Folge haben und deren Soll-Zahl
      der Dienst nicht kennt -> "unbekannt", dort koennte etwas fehlen.
    * Sonst, mit mindestens einer bewertbaren Staffel -> "vollstaendig".
    """
    if not sc:
        return "unknown", None
    regular = [r for r in seasons._status_for(per_season, sc) if r["s"] >= 1]
    if any(r["t"] and r["h"] - r["t"] > MAX_EXTRA_PER_SEASON for r in regular):
        return "unknown", None
    gaps = sum(max(0, (r["t"] or 0) - r["h"])
               for r in regular if r["st"] in (seasons.PARTIAL, seasons.NONE))
    if gaps:
        return "incomplete", gaps
    blind = any(r["st"] == seasons.UNKNOWN and r["h"] == 0 for r in regular)
    if blind or not any(r["st"] == seasons.FULL for r in regular):
        return "unknown", None
    return "complete", 0


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
            completeness, missing = _judge(per_season, sc)
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
