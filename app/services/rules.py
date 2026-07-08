"""Regel-Engine: setzt automatisch Tags anhand definierbarer Bedingungen.

Regel = {match_type: 'all'|'any', conditions: [...], actions: [...]}.
Bedingung = {field, op, value}. NICHT wird ueber not_equals/not_contains
ausgedrueckt. Aktion = {type:'add_tag', tag_id}.
"""
import json
from datetime import datetime, timezone

from .. import db

LIST_FIELDS = {"genres", "audio_langs", "subtitle_langs", "audio_codecs"}
# Felder, die in Regeln verwendet werden duerfen (aus media_items).
FIELDS = [
    "item_type", "library_name", "official_rating", "community_rating", "year",
    "genres", "audio_langs", "subtitle_langs", "audio_codecs", "video_codec",
    "resolution", "height", "width", "hdr", "completeness", "missing_episodes",
    "fsk_suspicious", "status", "runtime_min",
]
OPS = ["equals", "not_equals", "contains", "not_contains",
       "gt", "lt", "gte", "lte", "is_empty", "is_not_empty"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def eval_condition(item: dict, cond: dict) -> bool:
    field, op, val = cond.get("field"), cond.get("op"), cond.get("value")
    actual = item.get(field)

    if field in LIST_FIELDS:
        lst = [str(x).lower() for x in (actual or [])]
        v = str(val).lower()
        if op == "contains":
            return v in lst
        if op == "not_contains":
            return v not in lst
        if op == "is_empty":
            return len(lst) == 0
        if op == "is_not_empty":
            return len(lst) > 0
        return False

    if op == "is_empty":
        return actual is None or actual == ""
    if op == "is_not_empty":
        return not (actual is None or actual == "")
    if op in ("gt", "lt", "gte", "lte"):
        a, b = _num(actual), _num(val)
        if a is None or b is None:
            return False
        return {"gt": a > b, "lt": a < b, "gte": a >= b, "lte": a <= b}[op]

    s_actual = "" if actual is None else str(actual).lower()
    s_val = str(val).lower()
    if op == "equals":
        return s_actual == s_val
    if op == "not_equals":
        return s_actual != s_val
    if op == "contains":
        return s_val in s_actual
    if op == "not_contains":
        return s_val not in s_actual
    return False


def eval_rule(item: dict, rule: dict) -> bool:
    conds = rule.get("_conditions") or []
    if not conds:
        return False
    results = [eval_condition(item, c) for c in conds]
    return all(results) if rule.get("match_type", "all") == "all" else any(results)


# -- CRUD -------------------------------------------------------------------
def list_rules() -> list:
    return [dict(r) for r in db.query("SELECT * FROM rules ORDER BY priority, id")]


def create_rule(name, match_type, conditions, actions, priority=100, enabled=1) -> int:
    return db.execute(
        "INSERT INTO rules(name, enabled, priority, match_type, conditions, actions, created_at)"
        " VALUES(?,?,?,?,?,?,?)",
        (name, enabled, priority, match_type, json.dumps(conditions), json.dumps(actions), _now()),
    )


def update_rule(rule_id, name, match_type, conditions, actions, priority, enabled) -> None:
    db.execute(
        "UPDATE rules SET name=?, enabled=?, priority=?, match_type=?, conditions=?, actions=?"
        " WHERE id=?",
        (name, enabled, priority, match_type, json.dumps(conditions), json.dumps(actions), rule_id),
    )


def delete_rule(rule_id) -> None:
    db.execute("DELETE FROM rules WHERE id=?", (rule_id,))


# -- Ausfuehrung ------------------------------------------------------------
def _load_items(conn) -> list:
    cols = "id, " + ", ".join(FIELDS)
    items = []
    for row in conn.execute(f"SELECT {cols} FROM media_items"):
        item = dict(row)
        for jf in LIST_FIELDS:
            item[jf] = json.loads(item.get(jf) or "[]")
        items.append(item)
    return items


def apply_all() -> dict:
    """Automatische Tags neu berechnen. Manuelle Zuordnungen bleiben unberuehrt."""
    rules = list_rules()
    for r in rules:
        r["_conditions"] = json.loads(r.get("conditions") or "[]")
        r["_actions"] = json.loads(r.get("actions") or "[]")
    active = [r for r in rules if r.get("enabled")]

    assignments = 0
    with db.get_conn() as conn:
        conn.execute("DELETE FROM item_tags WHERE auto=1")
        items = _load_items(conn)
        for item in items:
            for rule in active:
                if not eval_rule(item, rule):
                    continue
                for action in rule["_actions"]:
                    if action.get("type") == "add_tag" and action.get("tag_id"):
                        conn.execute(
                            "INSERT INTO item_tags(item_id, tag_id, auto) VALUES(?,?,1) "
                            "ON CONFLICT(item_id, tag_id) DO NOTHING",
                            (item["id"], action["tag_id"]),
                        )
                        assignments += 1
        conn.commit()
    return {"rules": len(active), "assignments": assignments}
