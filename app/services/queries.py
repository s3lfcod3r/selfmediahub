"""Leseabfragen für die Ansichten - immer aus der eigenen lokalen DB."""
import json

from .. import db
from . import ratings, settings as settings_service, tags as tags_service

_JSON_COLS = ("genres", "audio_codecs", "audio_langs", "subtitle_langs", "season_status")


def _parse(row: dict) -> dict:
    item = dict(row)
    for col in _JSON_COLS:
        item[col] = json.loads(item.get(col) or "[]")
    # Rohe Soll-Zahlen je Staffel braucht nur seasons.recompute - aus dem an die
    # Seite eingebetteten JSON raushalten (window.__DATA__ enthaelt ALLE Items).
    item.pop("tmdb_season_counts", None)
    item.pop("tvdb_orders", None)  # nur fuer die Detail-Order-Logik, nicht in die Liste
    # Cover ueber den eigenen Bild-Proxy ausliefern (Roh-URL der Quelle bleibt in der DB).
    if item.get("image_url"):
        item["image_url"] = f"/api/image/{item['id']}"
    return item


def _acked_set() -> set:
    return {(r["source_ref"], r["source_id"])
            for r in db.query("SELECT source_ref, source_id FROM fsk_acks")}


def _display(raw, art: str, translate: bool):
    """(text, xlated). Bei ``translate`` in die bevorzugte Rating-Art umrechnen
    (Phase 5c); sonst den ROHEN Quellwert unveraendert zeigen (Phase 5d, Fix 3).
    ``xlated`` (Hinweis-Symbol) gibt es nur im uebersetzten Modus."""
    if not raw:
        return None, 0
    if not translate:
        return str(raw), 0
    disp, xlated = ratings.translate(raw, art)
    # Fallback: nicht erkannter Rohwert -> unveraendert zeigen statt zu verschlucken.
    return (disp if disp is not None else str(raw)), (1 if xlated else 0)


def _add_rating_display(item: dict, art: str, translate: bool) -> None:
    """Anzeige-Felder fuer Quelle/Vorschlag/Drift setzen. Das Alter (fuer die
    Filter-/Handlungsbedarf-Logik) wird IMMER berechnet, unabhaengig vom
    Uebersetzen-Schalter."""
    item["rating_disp"], item["rating_xlated"] = _display(item.get("official_rating"), art, translate)
    item["rating_age"] = ratings.age_of(item.get("official_rating"))
    item["suggested_disp"], item["suggested_xlated"] = _display(item.get("fsk_suggested"), art, translate)
    item["suggested_age"] = ratings.age_of(item.get("fsk_suggested"))
    # Drift (5c.5): SelfMediaHub hat mal geschrieben, Emby weicht jetzt ab. Vergleich
    # ueber das ALTER - format-tolerant (Emby gibt den Wert evtl. anders zurueck).
    written = item.get("rating_written")
    item["rating_drift"] = 1 if (written is not None
                                 and ratings.age_of(written) != item["rating_age"]) else 0
    item["written_disp"], _ = _display(written, art, translate)
    item["written_age"] = ratings.age_of(written)


def get_items() -> list:
    rows = db.query("SELECT * FROM media_items ORDER BY sort_name COLLATE NOCASE")
    tagmap = tags_service.tags_for_items()
    acked = _acked_set()
    art = settings_service.get("display.rating_art", ratings.DEFAULT_ART)
    translate = bool(settings_service.get("display.rating_translate", False))
    items = []
    for row in rows:
        item = _parse(row)
        item["tags"] = tagmap.get(item["id"], [])
        item["fsk_acked"] = 1 if (item["source_ref"], item["source_id"]) in acked else 0
        _add_rating_display(item, art, translate)
        items.append(item)
    return items


def get_item(item_id: int):
    rows = db.query("SELECT * FROM media_items WHERE id=?", (item_id,))
    if not rows:
        return None
    item = _parse(rows[0])
    item["fsk_acked"] = 1 if (item["source_ref"], item["source_id"]) in _acked_set() else 0
    return item


def get_libraries() -> list:
    rows = db.query(
        "SELECT DISTINCT library_name FROM media_items "
        "WHERE library_name IS NOT NULL AND library_name <> '' "
        "ORDER BY library_name"
    )
    return [r["library_name"] for r in rows]


def compute_stats(items: list) -> dict:
    return {
        "total": len(items),
        "films": sum(1 for i in items if i["item_type"] == "Film"),
        "series": sum(1 for i in items if i["item_type"] == "Serie"),
        "no_rating": sum(1 for i in items if not i.get("official_rating")),
        # unbearbeitet = hat eine Freigabe, aber (noch) nicht in Emby gesperrt/angefasst
        "unreviewed": sum(1 for i in items
                          if i.get("official_rating") and not i.get("rating_locked")),
        # abgewichen = seit SMHs letztem Schreiben ausserhalb geaendert (5c.5)
        "drifted": sum(1 for i in items if i.get("rating_drift")),
        "incomplete": sum(1 for i in items if i.get("completeness") == "incomplete"),
        "suspicious": sum(1 for i in items if i.get("fsk_suspicious")),
        "uhd": sum(1 for i in items if i.get("resolution") == "4K"),
    }
