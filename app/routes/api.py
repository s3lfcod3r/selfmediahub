"""JSON-API: Sync, Tags, Regeln, FSK-Schreiben, Bild-Proxy."""
import requests
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from .. import config, db
from ..services import (
    auth, completeness, coverage, episode_order, fsk,
    providers as providers_service, queries, rules,
    seasons, settings as settings_service, sources as sources_service,
    sync as sync_service, tags, tmdb, updatecheck,
)

router = APIRouter(prefix="/api")

# Cover werden ueber den Container ausgeliefert (Browser erreicht die Quelle - z.B.
# Emby im Docker-Netz - oft nicht direkt). 1 Tag Browser-Cache.
_IMAGE_CACHE = "public, max-age=86400"
_IMAGE_TIMEOUT = 20


def _fail(exc: Exception):
    raise HTTPException(status_code=500, detail=str(exc))


# -- Sync -------------------------------------------------------------------
@router.post("/sync")
def api_sync():
    """Startet den Sync im Hintergrund und kehrt sofort zurück."""
    return {"ok": True, **sync_service.start_background()}


@router.get("/sync/status")
def api_sync_status():
    return sync_service.get_state()


# -- Bild-Proxy -------------------------------------------------------------
@router.get("/image/{item_id}")
def api_image(item_id: int):
    """Cover serverseitig von der Quelle holen und an den Browser durchreichen.

    Loest das Problem, dass die Bild-URL (z.B. Emby im Docker-Netz) fuer den
    Browser nicht erreichbar ist. Es wird nur die zum Item gespeicherte URL
    geladen - keine beliebigen Adressen (kein SSRF-Einfallstor).
    """
    rows = db.query("SELECT image_url FROM media_items WHERE id=?", (item_id,))
    url = rows[0]["image_url"] if rows else None
    if not url:
        raise HTTPException(status_code=404, detail="Kein Bild")
    try:
        resp = requests.get(url, timeout=_IMAGE_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="Bild konnte nicht geladen werden")
    return Response(
        content=resp.content,
        media_type=resp.headers.get("Content-Type", "image/jpeg"),
        headers={"Cache-Control": _IMAGE_CACHE},
    )


# -- Detailansicht (Item + Episoden aus der DB) -----------------------------
@router.get("/items/{item_id}/detail")
def api_item_detail(item_id: int):
    item = queries.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Eintrag nicht gefunden")
    item["tags"] = tags.tags_for_items().get(item_id, [])

    episodes, note, missing, season_summary, order_meta = [], None, [], None, None
    if item["item_type"] == "Serie":
        episodes = db.get_episodes(item_id)
        if not episodes:
            note = "Noch keine Episoden gespeichert - bitte einmal neu einlesen."

        # Soll-Struktur aus der aufgeloesten Reihenfolge (Aired/DVD/Absolut) - nicht
        # mehr fest gegen TMDb-Aired, sondern gegen die je Serie gewaehlte Nummerierung.
        struct = db.query(
            "SELECT tmdb_season_counts, tvdb_orders, episode_order, "
            "episode_order_resolved, tmdb_episodes FROM media_items WHERE id=?",
            (item_id,),
        )[0]
        sc, _total = episode_order.effective_structure(struct)
        order_opts = [o for o in ("aired", "dvd", "absolute")
                      if o in episode_order._orders_of(struct)]
        order_meta = {"options": order_opts,
                      "pref": struct["episode_order"] or "auto",
                      "resolved": struct["episode_order_resolved"] or "aired"}

        # Konkret fehlende Episoden bestimmen. Staffel 0 (Specials) bleibt aussen vor
        # (konsistent zur Vollstaendigkeit), bleibt aber in der Episodenliste sichtbar.
        if episodes and sc:
            present = [(e["season"], e["episode"]) for e in episodes
                       if (e.get("season") or 0) >= 1 and e.get("episode") is not None]
            missing = tmdb.compute_missing(sc, present)
            for m in missing:
                episodes.append({"season": m["season"], "episode": m["episode"],
                                 "name": "", "missing": True})
            episodes.sort(key=lambda e: ((e["season"] if e["season"] is not None else 999),
                                         (e["episode"] if e["episode"] is not None else 999)))
            # Einzelfolgen nicht sicher zuzuordnen -> wenigstens Zahlen zeigen:
            # verlaesslich = Pro-Staffel-Summen, sonst wenigstens die Gesamtzahl.
            if not missing and item.get("completeness") == "incomplete":
                summ = tmdb.season_summary(sc, present)
                if summ["total_tmdb"] > 0:
                    season_summary = summ
                elif not note:
                    note = ("Fehlende Folgen lassen sich hier nicht sicher bestimmen - "
                            "die Staffelnummerierung in Emby weicht ab.")
        elif episodes and not sc and item.get("completeness") == "incomplete":
            # Keine Soll-Struktur (kein TMDb/TheTVDB-Abgleich) - wenigstens Gesamtzahl.
            miss = item.get("missing_episodes")
            note = note or (
                "Fehlende Folgen werden für diesen Titel nicht einzeln aufgeschlüsselt "
                "(kein Metadaten-Abgleich)"
                + (f" - es fehlen laut Anbieter {miss} Folgen." if miss else "."))

    return {"item": item, "episodes": episodes, "note": note,
            "season_summary": season_summary, "order": order_meta,
            "missing_count": len(missing), "allow_write": config.ALLOW_EMBY_WRITE}


# -- Episoden-Reihenfolge je Serie (Aired/DVD/Absolut) ----------------------
@router.post("/items/{item_id}/order")
async def api_item_order(item_id: int, request: Request):
    """Reihenfolge fuer eine Serie festlegen ('auto' = Laufzeit-Vorwahl) und die
    abgeleiteten Werte (Vollstaendigkeit, Staffel-Ampeln) sofort neu rechnen."""
    d = await request.json()
    order = (d.get("order") or "auto").strip().lower()
    if order not in ("auto", "aired", "dvd", "absolute"):
        raise HTTPException(status_code=400, detail="Ungültige Reihenfolge")
    db.execute("UPDATE media_items SET episode_order=? WHERE id=?",
               (None if order == "auto" else order, item_id))
    episode_order.recompute()
    completeness.recompute()
    seasons.recompute()
    return {"ok": True}


# -- Metadaten für den Regel-Builder --------------------------------------
@router.get("/meta/fields")
def api_fields():
    return {"fields": rules.FIELDS, "ops": rules.OPS, "tags": tags.list_tags()}


# -- Account ----------------------------------------------------------------
@router.get("/account")
def api_account():
    return auth.get_account() or {}


@router.post("/account/username")
async def api_account_username(request: Request):
    d = await request.json()
    username = (d.get("username") or "").strip()
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Benutzername zu kurz (min. 3 Zeichen)")
    auth.set_username(username)
    return {"ok": True}


@router.post("/account/email")
async def api_account_email(request: Request):
    d = await request.json()
    auth.set_email((d.get("email") or "").strip())
    return {"ok": True}


@router.post("/account/password")
async def api_account_password(request: Request):
    d = await request.json()
    acc = auth.get_account()
    if not acc or not auth.verify_login(acc["username"], d.get("current") or ""):
        raise HTTPException(status_code=400, detail="Aktuelles Passwort ist falsch")
    new = d.get("new") or ""
    if len(new) < 8:
        raise HTTPException(status_code=400, detail="Neues Passwort zu kurz (min. 8 Zeichen)")
    auth.set_password(new)
    return {"ok": True}


@router.post("/account/auth")
async def api_account_auth(request: Request):
    d = await request.json()
    auth.set_auth_enabled(bool(d.get("enabled")))
    return {"ok": True, "enabled": auth.auth_enabled()}


# -- Update-Pruefung --------------------------------------------------------
@router.get("/update")
def api_update():
    return updatecheck.get_status()


@router.post("/update/check")
def api_update_check():
    return updatecheck.check_now()


# -- Einstellungen ----------------------------------------------------------
@router.get("/settings")
def api_settings():
    return {"settings": settings_service.all_settings()}


@router.post("/settings")
async def api_settings_save(request: Request):
    data = await request.json()
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Objekt (key/value) erwartet")
    clean = {k: v for k, v in data.items() if k in settings_service.allowed_keys()}
    lang_changed = ("display.primary_language" in clean
                    and clean["display.primary_language"] != settings_service.get("display.primary_language"))
    settings_service.save_many(clean)
    # Primaere Sprache geaendert -> Abdeckung sofort aus der DB neu berechnen (kein Sync noetig)
    if lang_changed:
        try:
            coverage.recompute()
        except Exception:  # noqa: BLE001
            pass
    return {"ok": True, "saved": sorted(clean), "settings": settings_service.all_settings()}


# -- Datenquellen (Phase 4a) ------------------------------------------------
@router.get("/sources")
def api_sources_list():
    return {"sources": sources_service.list_sources(),
            "kinds": list(sources_service.KINDS),
            "server_kinds": list(sources_service.SERVER_KINDS)}


@router.post("/sources")
async def api_source_create(request: Request):
    d = await request.json()
    try:
        sid = sources_service.create_source(
            (d.get("kind") or "").strip(), d.get("name") or "",
            d.get("base_url") or "", d.get("secret") or "",
            d.get("local_paths"), d.get("libraries"), d.get("enabled", True),
        )
        return {"ok": True, "id": sid}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/sources/{source_id}")
async def api_source_update(source_id: int, request: Request):
    d = await request.json()
    # Leeres Secret-Feld = Key behalten (None); nur ein echter Wert ersetzt ihn.
    secret = d.get("secret")
    try:
        sources_service.update_source(
            source_id,
            name=d.get("name"), base_url=d.get("base_url"),
            secret=(secret if secret else None),
            local_paths=d.get("local_paths"), libraries=d.get("libraries"),
            enabled=d.get("enabled"),
        )
        return {"ok": True}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/sources/{source_id}")
def api_source_delete(source_id: int):
    sources_service.delete_source(source_id)
    return {"ok": True}


@router.post("/sources/{source_id}/test")
def api_source_test(source_id: int):
    try:
        sources_service.test_connection(source_id)
        return {"ok": True}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # noqa: BLE001 - Verbindungsfehler an die UI melden
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/sources/{source_id}/libraries")
def api_source_libraries(source_id: int):
    try:
        return {"libraries": sources_service.list_libraries(source_id)}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # noqa: BLE001 - Verbindungsfehler an die UI melden
        raise HTTPException(status_code=400, detail=str(exc))


# -- Metadaten-Dienste (Phase 5c): zwei feste Dienste -----------------------
@router.get("/providers")
def api_providers_list():
    return {"providers": providers_service.list_providers(),
            "labels": providers_service.KIND_LABELS}


@router.put("/providers/{kind}")
async def api_provider_set(kind: str, request: Request):
    d = await request.json()
    # Leeres Key-Feld = Key behalten (None); nur ein echter Wert ersetzt ihn.
    api_key = d.get("api_key")
    try:
        providers_service.set_provider(
            kind, api_key=(api_key if api_key else None), enabled=d.get("enabled"),
        )
        return {"ok": True}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


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
@router.post("/fsk/ack")
async def api_fsk_ack(request: Request):
    """Einen FSK-Fall als 'passt so' bestätigen (überlebt Re-Sync)."""
    d = await request.json()
    rows = db.query("SELECT source_kind, source_id, source_ref FROM media_items WHERE id=?",
                    (int(d["item_id"]),))
    if not rows:
        raise HTTPException(status_code=404, detail="Eintrag nicht gefunden")
    db.execute(
        "INSERT INTO fsk_acks(source_kind, source_id, source_ref) VALUES(?, ?, ?) "
        "ON CONFLICT(source_ref, source_id) DO NOTHING",
        (rows[0]["source_kind"], rows[0]["source_id"], rows[0]["source_ref"]),
    )
    return {"ok": True}


@router.delete("/fsk/ack/{item_id}")
def api_fsk_unack(item_id: int):
    rows = db.query("SELECT source_id, source_ref FROM media_items WHERE id=?", (item_id,))
    if rows:
        db.execute("DELETE FROM fsk_acks WHERE source_ref=? AND source_id=?",
                   (rows[0]["source_ref"], rows[0]["source_id"]))
    return {"ok": True}


@router.post("/fsk/write-bulk")
async def api_fsk_write_bulk(request: Request):
    """Mehrere FSK-Freigaben auf einmal nach Emby schreiben."""
    d = await request.json()
    changes = d.get("changes", [])
    saved, errors = 0, []
    for ch in changes:
        rows = db.query("SELECT source_kind, source_id, source_ref FROM media_items WHERE id=?",
                        (int(ch["item_id"]),))
        if not rows:
            errors.append({"item_id": ch["item_id"], "error": "nicht gefunden"})
            continue
        r = dict(rows[0])
        if r["source_kind"] != "emby":
            errors.append({"item_id": ch["item_id"], "error": "nur Emby"})
            continue
        rating = (ch.get("rating") or "").strip()
        try:
            fsk.write_emby(r["source_ref"], r["source_id"], rating or None)
            # write_emby sperrt das Feld -> rating_locked sofort setzen (Ampel gruen);
            # rating_written merkt den Wert als Drift-Basis (5c.5).
            db.execute("UPDATE media_items SET official_rating=?, rating_locked=1, "
                       "rating_written=?, fsk_suspicious=0, fsk_reason='' WHERE id=?",
                       (rating, rating, int(ch["item_id"])))
            saved += 1
        except Exception as exc:  # noqa: BLE001
            errors.append({"item_id": ch["item_id"], "error": str(exc)})
    return {"ok": True, "saved": saved, "errors": errors}


@router.post("/fsk/write")
async def api_fsk_write(request: Request):
    d = await request.json()
    rows = db.query("SELECT * FROM media_items WHERE id=?", (int(d["item_id"]),))
    if not rows:
        raise HTTPException(status_code=404, detail="Eintrag nicht gefunden")
    item = dict(rows[0])
    if item["source_kind"] != "emby":
        raise HTTPException(status_code=400, detail="Schreiben nur für Emby-Quellen möglich")
    # "rating" im Body (auch leer) = expliziter Wunsch; sonst Vorschlag nutzen.
    if "rating" in d:
        rating = (d.get("rating") or "").strip()
    else:
        rating = item.get("fsk_suggested") or item.get("official_rating") or ""
    try:
        fsk.write_emby(item["source_ref"], item["source_id"], rating or None)
        # write_emby sperrt das Feld -> rating_locked sofort setzen (Ampel gruen);
        # rating_written merkt den Wert als Drift-Basis (5c.5).
        db.execute("UPDATE media_items SET official_rating=?, rating_locked=1, "
                   "rating_written=?, fsk_suspicious=0, fsk_reason='' WHERE id=?",
                   (rating, rating, item["id"]))
        return {"ok": True, "rating": rating or "(entfernt)"}
    except Exception as exc:  # noqa: BLE001
        _fail(exc)


@router.post("/fsk/refresh-locks")
def api_fsk_refresh_locks():
    """Sperr-Status (LockedFields) fuer alle Emby/Jellyfin-Items frisch aus der
    Quelle lesen. Read-only gegen die Quelle - noetig, weil der Listen-Sync die
    Sperre nicht mitbekommt (Emby liefert LockedFields nur im Einzel-Item)."""
    try:
        return {"ok": True, **fsk.refresh_locks()}
    except Exception as exc:  # noqa: BLE001
        _fail(exc)


@router.post("/fsk/accept-drift")
async def api_fsk_accept_drift(request: Request):
    """Externe Aenderung als neue Basis akzeptieren (5c.5): rating_written = aktueller Wert.
    Schreibt NICHT nach Emby - loescht nur den 'abgewichen'-Zustand."""
    d = await request.json()
    rows = db.query("SELECT id, official_rating FROM media_items WHERE id=?", (int(d["item_id"]),))
    if not rows:
        raise HTTPException(status_code=404, detail="Eintrag nicht gefunden")
    db.execute("UPDATE media_items SET rating_written=? WHERE id=?",
               (rows[0]["official_rating"] or "", rows[0]["id"]))
    return {"ok": True}
