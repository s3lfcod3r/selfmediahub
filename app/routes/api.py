"""JSON-API: Sync, Tags, Regeln, FSK-Schreiben."""
from fastapi import APIRouter, HTTPException, Request

from .. import config, db
from ..services import fsk, queries, rules, sync as sync_service, tags

router = APIRouter(prefix="/api")


def _fail(exc: Exception):
    raise HTTPException(status_code=500, detail=str(exc))


# -- Sync -------------------------------------------------------------------
@router.post("/sync")
def api_sync():
    """Startet den Sync im Hintergrund und kehrt sofort zurueck."""
    return {"ok": True, **sync_service.start_background()}


@router.get("/sync/status")
def api_sync_status():
    return sync_service.get_state()


# -- Detailansicht (Item + Episoden live) -----------------------------------
@router.get("/items/{item_id}/detail")
def api_item_detail(item_id: int):
    item = queries.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Eintrag nicht gefunden")
    item["tags"] = tags.tags_for_items().get(item_id, [])

    episodes, note = [], None
    if item["item_type"] == "Serie":
        conn = sync_service.connector_for(item["source_kind"])
        if conn is not None and hasattr(conn, "fetch_episodes"):
            try:
                episodes = conn.fetch_episodes(item["source_id"])
            except Exception as exc:  # noqa: BLE001
                note = f"Episoden konnten nicht geladen werden: {exc}"
        else:
            note = "Episodendetails sind fuer diese Quelle nicht verfuegbar."
    return {"item": item, "episodes": episodes, "note": note}


# -- Metadaten fuer den Regel-Builder --------------------------------------
@router.get("/meta/fields")
def api_fields():
    return {"fields": rules.FIELDS, "ops": rules.OPS, "tags": tags.list_tags()}


# -- Tags -------------------------------------------------------------------
@router.get("/tags")
def api_tags():
    return {"tags": tags.list_tags()}


@router.post("/tags")
async def api_tag_create(request: Request):
    d = await request.json()
    if not (d.get("name") or "").strip():
        raise HTTPException(status_code=400, detail="Name fehlt")
    try:
        tid = tags.create_tag(d["name"], d.get("color") or "#33a78c",
                              d.get("icon") or "", int(d.get("priority") or 100))
        return {"ok": True, "id": tid}
    except Exception as exc:  # noqa: BLE001
        _fail(exc)


@router.put("/tags/{tag_id}")
async def api_tag_update(tag_id: int, request: Request):
    d = await request.json()
    tags.update_tag(tag_id, d.get("name", ""), d.get("color") or "#33a78c",
                    d.get("icon") or "", int(d.get("priority") or 100))
    return {"ok": True}


@router.delete("/tags/{tag_id}")
def api_tag_delete(tag_id: int):
    tags.delete_tag(tag_id)
    return {"ok": True}


@router.post("/items/{item_id}/tags")
async def api_item_tag_add(item_id: int, request: Request):
    d = await request.json()
    tags.add_manual(item_id, int(d["tag_id"]))
    return {"ok": True}


@router.delete("/items/{item_id}/tags/{tag_id}")
def api_item_tag_remove(item_id: int, tag_id: int):
    tags.remove(item_id, tag_id)
    return {"ok": True}


# -- Regeln -----------------------------------------------------------------
@router.get("/rules")
def api_rules():
    return {"rules": rules.list_rules()}


@router.post("/rules")
async def api_rule_create(request: Request):
    d = await request.json()
    rid = rules.create_rule(
        d.get("name", "Regel"), d.get("match_type", "all"),
        d.get("conditions", []), d.get("actions", []),
        int(d.get("priority") or 100), 1 if d.get("enabled", True) else 0,
    )
    return {"ok": True, "id": rid}


@router.put("/rules/{rule_id}")
async def api_rule_update(rule_id: int, request: Request):
    d = await request.json()
    rules.update_rule(
        rule_id, d.get("name", "Regel"), d.get("match_type", "all"),
        d.get("conditions", []), d.get("actions", []),
        int(d.get("priority") or 100), 1 if d.get("enabled", True) else 0,
    )
    return {"ok": True}


@router.delete("/rules/{rule_id}")
def api_rule_delete(rule_id: int):
    rules.delete_rule(rule_id)
    return {"ok": True}


@router.post("/rules/apply")
def api_rules_apply():
    try:
        return {"ok": True, **rules.apply_all()}
    except Exception as exc:  # noqa: BLE001
        _fail(exc)


# -- FSK schreiben (Ausnahme, nur mit ALLOW_EMBY_WRITE) ---------------------
@router.post("/fsk/write")
async def api_fsk_write(request: Request):
    d = await request.json()
    rows = db.query("SELECT * FROM media_items WHERE id=?", (int(d["item_id"]),))
    if not rows:
        raise HTTPException(status_code=404, detail="Eintrag nicht gefunden")
    item = dict(rows[0])
    if item["source_kind"] != "emby":
        raise HTTPException(status_code=400, detail="Schreiben nur fuer Emby-Quellen moeglich")
    rating = d.get("rating") or item.get("fsk_suggested") or item.get("official_rating")
    if not rating:
        raise HTTPException(status_code=400, detail="Keine Freigabe zum Schreiben")
    try:
        fsk.write_emby(item["source_id"], rating)
        db.execute("UPDATE media_items SET official_rating=?, fsk_suspicious=0, fsk_reason='' WHERE id=?",
                   (rating, item["id"]))
        return {"ok": True, "rating": rating}
    except Exception as exc:  # noqa: BLE001
        _fail(exc)
