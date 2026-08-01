"""Vollständigkeit je Serie: vorhandene vs. veröffentlichte Episoden (TMDb).

Wichtig: Beide Seiten zählen **nur reguläre Staffeln (>= 1)**. Staffel 0
(Specials) wird ausgeschlossen, weil TMDbs ``number_of_episodes`` die Specials
ebenfalls nicht mitzählt - sonst wäre die HABEN-Seite künstlich aufgebläht und
unvollständige Serien würden fälschlich als "vollständig" gelten.

Wird nach dem Episoden-Sync aufgerufen (die Einzelfolgen liegen dann in der DB).
"""
from .. import db
from . import episode_order, seasons


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
    # Alle Episoden einmal laden (kein N+1): je Serie die regulaeren Folgen
    # (season >= 1) je Staffel zaehlen und merken, welche Serien Episoden haben.
    have_by_season: dict = {}
    has_episodes: set = set()
    for e in db.query("SELECT item_id, season FROM episodes"):
        has_episodes.add(e["item_id"])
        s = e["season"] or 0
        if s >= 1:  # Staffel 0 (Specials) zaehlt nicht mit
            have_by_season.setdefault(e["item_id"], {})[s] = \
                have_by_season.get(e["item_id"], {}).get(s, 0) + 1

    updates = []
    for row in db.query(
        "SELECT id, tmdb_episodes, have_episodes, tmdb_season_counts, tvdb_orders, "
        "episode_order_resolved FROM media_items WHERE item_type='Serie'"
    ):
        per_season = have_by_season.get(row["id"], {})
        if row["id"] in has_episodes:
            have = sum(per_season.values())  # 0 wenn nur Specials vorhanden
        else:
            have = row["have_episodes"]  # noch keine Episoden gespeichert

        # Soll-Struktur + Gesamtzahl aus der aufgeloesten Reihenfolge.
        sc, total = episode_order.effective_structure(row)
        # Nur werten, wenn die Nummerierung zuordenbar ist (identisch zum Cover).
        # Ohne gespeicherte Einzelfolgen kann nicht geprueft werden -> Struktur
        # vorhanden = best effort wie bisher.
        reliable = seasons._is_reliable(per_season, sc) if per_season else bool(sc)
        if total and have is not None and reliable:
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
