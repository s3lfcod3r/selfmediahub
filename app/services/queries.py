"""Leseabfragen für die Ansichten - immer aus der eigenen lokalen DB."""
import json

from .. import db
from . import tags as tags_service

_JSON_COLS = ("genres", "audio_codecs", "audio_langs", "subtitle_langs")


def _parse(row: dict) -> dict:
    item = dict(row)
    for col in _JSON_COLS:
        item[col] = json.loads(item.get(col) or "[]")
    return item


def _acked_set() -> set:
    return {(r["source_kind"], r["source_id"])
            for r in db.query("SELECT source_kind, source_id FROM fsk_acks")}


def get_items() -> list:
    rows = db.query("SELECT * FROM media_items ORDER BY sort_name COLLATE NOCASE")
    tagmap = tags_service.tags_for_items()
    acked = _acked_set()
    items = []
    for row in rows:
        item = _parse(row)
        item["tags"] = tagmap.get(item["id"], [])
        item["fsk_acked"] = 1 if (item["source_kind"], item["source_id"]) in acked else 0
        items.append(item)
    return items


def get_item(item_id: int):
    rows = db.query("SELECT * FROM media_items WHERE id=?", (item_id,))
    if not rows:
        return None
    item = _parse(rows[0])
    item["fsk_acked"] = 1 if (item["source_kind"], item["source_id"]) in _acked_set() else 0
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
        "incomplete": sum(1 for i in items if i.get("completeness") == "incomplete"),
        "suspicious": sum(1 for i in items if i.get("fsk_suspicious")),
        "uhd": sum(1 for i in items if i.get("resolution") == "4K"),
    }
