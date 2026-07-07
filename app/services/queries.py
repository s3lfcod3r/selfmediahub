"""Leseabfragen fuer die Ansichten - immer aus der eigenen lokalen DB."""
import json

from .. import db


def get_items() -> list:
    rows = db.query(
        "SELECT * FROM media_items ORDER BY sort_name COLLATE NOCASE"
    )
    items = []
    for row in rows:
        item = dict(row)
        item["genres"] = json.loads(item.get("genres") or "[]")
        items.append(item)
    return items


def get_libraries() -> list:
    rows = db.query(
        "SELECT DISTINCT library_name FROM media_items "
        "WHERE library_name IS NOT NULL AND library_name <> '' "
        "ORDER BY library_name"
    )
    return [row["library_name"] for row in rows]


def compute_stats(items: list) -> dict:
    films = sum(1 for i in items if i["item_type"] == "Film")
    series = sum(1 for i in items if i["item_type"] == "Serie")
    no_rating = sum(1 for i in items if not i.get("official_rating"))
    return {
        "total": len(items),
        "films": films,
        "series": series,
        "no_rating": no_rating,
    }
