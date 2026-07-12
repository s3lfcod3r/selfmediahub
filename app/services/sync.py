"""Import/Scan-Pipeline: liest alle Quellen, reichert an (parallel), speichert.

Läuft im Hintergrund mit Fortschritts-State, damit die UI nicht blockiert.
"""
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from .. import config, db
from ..connectors.emby import EmbyConnector
from ..connectors.jellyfin import JellyfinConnector
from ..connectors.local import LocalConnector
from ..connectors.plex import PlexConnector
from . import analysis, completeness, coverage, fsk, notify, rules, tmdb

# Wieviele TMDb-Abfragen gleichzeitig (TMDb erlaubt reichlich).
TMDB_WORKERS = 8
# TMDb-Felder, die aus einem frueheren Sync übernommen werden können.
_CARRY = ("tmdb_id", "tmdb_seasons", "tmdb_episodes", "status", "fsk_suggested")

_lock = threading.Lock()
_thread = None
_STATE = {"running": False, "phase": "", "processed": 0, "total": 0,
          "result": None, "error": None, "at": None}


# -- Fortschritt ------------------------------------------------------------
def get_state() -> dict:
    with _lock:
        return dict(_STATE)


def _set(**kw) -> None:
    with _lock:
        _STATE.update(kw)


def build_connectors() -> list:
    conns = []
    if config.emby_configured():
        conns.append(EmbyConnector(config.EMBY_URL, config.EMBY_API_KEY))
    if config.jellyfin_configured():
        conns.append(JellyfinConnector(config.JELLYFIN_URL, config.JELLYFIN_API_KEY))
    if config.plex_configured():
        conns.append(PlexConnector(config.PLEX_URL, config.PLEX_TOKEN))
    if config.local_configured():
        conns.append(LocalConnector(config.LOCAL_PATHS))
    return conns


def connector_for(kind: str):
    """Einzelnen Connector für eine Quelle bauen (z.B. für Detail-Abrufe)."""
    if kind == "emby" and config.emby_configured():
        return EmbyConnector(config.EMBY_URL, config.EMBY_API_KEY)
    if kind == "jellyfin" and config.jellyfin_configured():
        return JellyfinConnector(config.JELLYFIN_URL, config.JELLYFIN_API_KEY)
    if kind == "plex" and config.plex_configured():
        return PlexConnector(config.PLEX_URL, config.PLEX_TOKEN)
    return None


def _enrich_one(item: dict, existing: dict, cache: dict) -> None:
    analysis.enrich(item)
    prev = existing.get(item["source_id"])
    if prev and prev.get("tmdb_id"):
        # Bereits abgeglichen -> TMDb-Daten übernehmen, kein Netzabruf.
        for field in _CARRY:
            if item.get(field) is None:
                item[field] = prev.get(field)
        if not item.get("genres") and prev.get("genres"):
            item["genres"] = json.loads(prev.get("genres") or "[]")
    else:
        tmdb.enrich(item, cache)
    completeness.compute(item)
    fsk.analyze(item)


def _sync_episodes(connectors: list) -> None:
    """Fuer jede Serie die Episoden holen und in der DB ablegen (ersetzt bestehende)."""
    for conn in connectors:
        if not hasattr(conn, "fetch_episodes"):
            continue
        series = db.query(
            "SELECT id, source_id FROM media_items WHERE source_kind=? AND item_type='Serie'",
            (conn.kind,),
        )
        total = len(series)
        for idx, s in enumerate(series, 1):
            _set(phase=f"Lese Episoden ({conn.kind}) {idx}/{total} ...")
            try:
                db.replace_episodes(s["id"], conn.fetch_episodes(s["source_id"]))
            except Exception:  # noqa: BLE001 - eine kaputte Serie stoppt den Rest nicht
                pass


def run_sync() -> dict:
    """Vollen Re-Sync aller Quellen ausführen (aktualisiert den Fortschritt)."""
    connectors = build_connectors()
    if not connectors:
        raise RuntimeError("Keine Medienquelle konfiguriert.")

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cache: dict = {}
    groups, sources = [], []

    # 1) Alle Quellen einlesen (schnell) -----------------------------------
    for conn in connectors:
        _set(phase=f"Lese {conn.kind} ...")
        try:
            items = conn.fetch_items()
            existing = {
                r["source_id"]: dict(r)
                for r in db.query("SELECT * FROM media_items WHERE source_kind=?", (conn.kind,))
            }
            groups.append((conn, items, existing))
        except Exception as exc:  # noqa: BLE001 - kaputte Quelle stoppt Rest nicht
            sources.append({"kind": conn.kind, "ok": False, "error": str(exc)})

    total = sum(len(items) for _c, items, _e in groups)
    _set(total=total, processed=0, phase="Analysiere & gleiche mit TMDb ab ...")

    # 2) Anreichern (parallel) ---------------------------------------------
    processed = 0
    with ThreadPoolExecutor(max_workers=TMDB_WORKERS) as pool:
        futures = [
            pool.submit(_enrich_one, it, existing, cache)
            for _conn, items, existing in groups for it in items
        ]
        for fut in as_completed(futures):
            try:
                fut.result()
            except Exception:  # noqa: BLE001 - einzelnes Item darf nicht alles kippen
                pass
            processed += 1
            if processed % 20 == 0 or processed == total:
                _set(processed=processed)

    # 3) Speichern ----------------------------------------------------------
    total_seen, total_new = 0, 0
    for conn, items, _existing in groups:
        _set(phase=f"Speichere {conn.kind} ...")
        res = db.upsert_items(conn.kind, items, now)
        total_seen += res["seen"]
        total_new += len(res["new"])
        sources.append({"kind": conn.kind, "seen": res["seen"],
                        "new": len(res["new"]), "removed": res["removed"], "ok": True})

    # 4) Episoden je Serie speichern (fuer Sprach-Abdeckung, Staffel-Status) ----
    _sync_episodes([conn for conn, _i, _e in groups])

    # 5) Abdeckung der primaeren Sprache berechnen -------------------------------
    _set(phase="Berechne Sprach-Abdeckung ...")
    coverage.recompute()

    _set(phase="Wende Regeln an ...")
    rule_res = rules.apply_all()
    db.set_meta("last_sync", now)
    db.set_meta("last_sync_count", str(total_seen))

    if total_new:
        notify.send("new_items", f"{total_new} neue Einträge in der Mediathek", {"count": total_new})

    return {"count": total_seen, "new": total_new, "at": now,
            "sources": sources, "rules": rule_res}


# -- Hintergrundlauf --------------------------------------------------------
def _run_guarded() -> None:
    try:
        result = run_sync()
        _set(result=result, error=None, phase="Fertig",
             at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    except Exception as exc:  # noqa: BLE001
        _set(error=str(exc), phase="Fehler")
    finally:
        _set(running=False)


def start_background() -> dict:
    """Sync in einem Hintergrund-Thread starten. Nie zwei gleichzeitig."""
    global _thread
    with _lock:
        if _STATE.get("running"):
            return {"started": False, "running": True}
        _STATE.update({"running": True, "phase": "Starte ...", "processed": 0,
                       "total": 0, "result": None, "error": None})
    _thread = threading.Thread(target=_run_guarded, name="smh-sync", daemon=True)
    _thread.start()
    return {"started": True, "running": True}
