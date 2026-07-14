"""Vollständigkeit je Serie: vorhandene vs. veröffentlichte Episoden (TMDb).

Wichtig: Beide Seiten zählen **nur reguläre Staffeln (>= 1)**. Staffel 0
(Specials) wird ausgeschlossen, weil TMDbs ``number_of_episodes`` die Specials
ebenfalls nicht mitzählt - sonst wäre die HABEN-Seite künstlich aufgebläht und
unvollständige Serien würden fälschlich als "vollständig" gelten.

Wird nach dem Episoden-Sync aufgerufen (die Einzelfolgen liegen dann in der DB).
"""
from .. import db


def recompute() -> int:
    """completeness ('complete'|'incomplete'|'unknown') + missing_episodes je Serie.

    HABEN-Seite = gespeicherte Episoden mit ``season >= 1`` (ohne Specials). Sind
    für eine Serie noch keine Episoden gespeichert, greift als Rückfall das
    Emby-Aggregat ``have_episodes``. Gibt die Anzahl aktualisierter Serien zurück.
    """
    # Alle Episoden einmal laden (kein N+1): je Serie die regulaeren Folgen
    # (season >= 1) zaehlen und merken, welche Serien ueberhaupt Episoden haben.
    have_regular: dict = {}
    has_episodes: set = set()
    for e in db.query("SELECT item_id, season FROM episodes"):
        has_episodes.add(e["item_id"])
        if (e["season"] or 0) >= 1:  # Staffel 0 (Specials) zaehlt nicht mit
            have_regular[e["item_id"]] = have_regular.get(e["item_id"], 0) + 1

    updates = []
    for row in db.query(
        "SELECT id, tmdb_episodes, have_episodes FROM media_items WHERE item_type='Serie'"
    ):
        if row["id"] in has_episodes:
            have = have_regular.get(row["id"], 0)  # 0 wenn nur Specials vorhanden
        else:
            have = row["have_episodes"]  # noch keine Episoden gespeichert

        total = row["tmdb_episodes"]
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
