"""Leseabfragen für die Ansichten - immer aus der eigenen lokalen DB."""
import json

from .. import db
from . import ratings, settings as settings_service, tags as tags_service

_JSON_COLS = ("genres", "audio_codecs", "audio_langs", "subtitle_langs")


def _parse(row: dict) -> dict:
    item = dict(row)
    for col in _JSON_COLS:
        item[col] = json.loads(item.get(col) or "[]")
    # Cover ueber den eigenen Bild-Proxy ausliefern (Roh-URL der Quelle bleibt in der DB).
    if item.get("image_url"):
        item["image_url"] = f"/api/image/{item['id']}"
    return item


def _acked_set() -> set:
    return {(r["source_ref"], r["source_id"])
            for r in db.query("SELECT source_ref, source_id FROM fsk_acks")}


def _add_rating_display(item: dict, art: str) -> None:
    """Freigabe in die bevorzugte Rating-Art uebersetzen (Anzeige, Phase 5c).
    Setzt rating_disp (Text oder None) + rating_xlated (1 wenn umgerechnet)."""
    disp, xlated = ratings.translate(item.get("official_rating"), art)
    item["rating_disp"] = disp
    item["rating_xlated"] = 1 if xlated else 0
    sug_disp, _ = ratings.translate(item.get("fsk_suggested"), art)
    item["suggested_disp"] = sug_disp


def get_items() -> list:
    rows = db.query("SELECT * FROM media_items ORDER BY sort_name COLLATE NOCASE")
    tagmap = tags_service.tags_for_items()
    acked = _acked_set()
    art = settings_service.get("display.rating_art", ratings.DEFAULT_ART)
    items = []
    for row in rows:
        item = _parse(row)
        item["tags"] = tagmap.get(item["id"], [])
        item["fsk_acked"] = 1 if (item["source_ref"], item["source_id"]) in acked else 0
        _add_rating_display(item, art)
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
        "incomplete": sum(1 for i in items if i.get("completeness") == "incomplete"),
        "suspicious": sum(1 for i in items if i.get("fsk_suspicious")),
        "uhd": sum(1 for i in items if i.get("resolution") == "4K"),
    }
