"""Eigenes Tag-System: anlegen, verwalten, Items zuordnen (manuell + automatisch)."""
from datetime import datetime, timezone

from .. import db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def list_tags() -> list:
    return [dict(r) for r in db.query(
        "SELECT * FROM tags ORDER BY priority, name COLLATE NOCASE"
    )]


def create_tag(name: str, color: str = "#33a78c", icon: str = "", priority: int = 100) -> int:
    return db.execute(
        "INSERT INTO tags(name, color, icon, priority, created_at) VALUES(?,?,?,?,?)",
        (name.strip(), color, icon, priority, _now()),
    )


def update_tag(tag_id: int, name: str, color: str, icon: str, priority: int) -> None:
    db.execute(
        "UPDATE tags SET name=?, color=?, icon=?, priority=? WHERE id=?",
        (name.strip(), color, icon, priority, tag_id),
    )


def delete_tag(tag_id: int) -> None:
    db.execute("DELETE FROM tags WHERE id=?", (tag_id,))


def add_manual(item_id: int, tag_id: int) -> None:
    db.execute(
        "INSERT INTO item_tags(item_id, tag_id, auto) VALUES(?,?,0) "
        "ON CONFLICT(item_id, tag_id) DO UPDATE SET auto=0",
        (item_id, tag_id),
    )


def remove(item_id: int, tag_id: int) -> None:
    db.execute("DELETE FROM item_tags WHERE item_id=? AND tag_id=?", (item_id, tag_id))


def tags_for_items() -> dict:
    """{item_id: [ {id,name,color,icon,auto} ... ]} - eine Abfrage fuer alle."""
    rows = db.query(
        "SELECT it.item_id AS item_id, t.id AS id, t.name AS name, "
        "t.color AS color, t.icon AS icon, it.auto AS auto, t.priority AS priority "
        "FROM item_tags it JOIN tags t ON t.id = it.tag_id "
        "ORDER BY t.priority, t.name COLLATE NOCASE"
    )
    out = {}
    for r in rows:
        out.setdefault(r["item_id"], []).append(dict(r))
    return out
