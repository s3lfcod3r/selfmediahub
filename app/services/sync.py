"""Import/Scan-Pipeline: liest alle Quellen, reichert an (parallel), speichert.

Läuft im Hintergrund mit Fortschritts-State, damit die UI nicht blockiert.
"""
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from .. import db, i18n
from . import (
    analysis, completeness, coverage, episode_order, fsk, metaproviders, notify,
    providers, rules, seasons, settings as settings_service, sources,
)

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
    """Aktive Quellen aus der DB als Connectoren (Phase 4a)."""
    return sources.build_connectors()


def connector_for(kind: str):
    """Einzelnen Connector einer aktiven Quelle bauen (z.B. für Detail-Abrufe)."""
    return sources.connector_for(kind)


def _already_enriched(prev: dict, is_series: bool, tvdb_on: bool) -> bool:
    """Ist eine Serie/ein Film wirklich schon bei TMDb angereichert?

    NICHT an ``tmdb_id`` festmachen: die liefert Emby gratis mit (ProviderIds),
    sie steht also auch dann, wenn der eigentliche TMDb-Abruf nie durchlief. Als
    "fertig"-Signal zählt das Feld, das erst der Abruf setzt - bei Serien die
    Episodenzahl, bei Filmen der Status. Sonst würden unfertige Einträge bei
    jedem Re-Sync übersprungen und blieben für immer leer.

    Bei Serien zählt zusätzlich ``tmdb_season_counts`` (Soll-Folgen je Staffel,
    für die Staffel-Badges). Das Feld kam später dazu: ohne diese Bedingung
    gälten alle Bestandsserien als fertig, der Abruf bliebe aus und die Staffel-
    Badges wären dauerhaft grau. So holt der erste Sync nach dem Update die
    Zahlen einmalig nach.
    """
    if not prev or not prev.get("tmdb_id"):
        return False
    if is_series:
        if (prev.get("tmdb_episodes") is None
                or prev.get("tmdb_season_counts") is None):
            return False
        # Bestandsserien einmalig nachladen, damit die Reihenfolgen (tvdb_orders)
        # fuer die Aired/DVD-Erkennung vorliegen - nur wenn TheTVDB aktiv ist.
        if tvdb_on and prev.get("tvdb_orders") is None:
            return False
        return True
    return prev.get("status") is not None


def _enrich_one(item: dict, existing: dict, cache: dict, tvdb_on: bool) -> None:
    analysis.enrich(item)
    prev = existing.get(item["source_id"])
    if _already_enriched(prev, item.get("item_type") == "Serie", tvdb_on):
        # Bereits vollständig abgeglichen -> TMDb-Daten übernehmen, kein Netzabruf.
        for field in _CARRY:
            if item.get(field) is None:
                item[field] = prev.get(field)
        if not item.get("genres") and prev.get("genres"):
            item["genres"] = json.loads(prev.get("genres") or "[]")
        # JSON-Spalten kommen als String aus der DB und muessen zurueck in die
        # Python-Struktur - der Upsert serialisiert sie sonst ein zweites Mal.
        if not item.get("tmdb_season_counts") and prev.get("tmdb_season_counts"):
            item["tmdb_season_counts"] = json.loads(prev.get("tmdb_season_counts") or "[]")
        if not item.get("tvdb_orders") and prev.get("tvdb_orders"):
            item["tvdb_orders"] = json.loads(prev.get("tvdb_orders") or "null")
    else:
        metaproviders.enrich_item(item, cache)
    fsk.analyze(item)


def _sync_episodes(connectors: list, lang: str) -> None:
    """Fuer jede Serie die Episoden holen und in der DB ablegen (ersetzt bestehende)."""
    for conn in connectors:
        if not hasattr(conn, "fetch_episodes"):
            continue
        series = db.query(
            "SELECT id, source_id FROM media_items WHERE source_ref=? AND item_type='Serie'",
            (conn.source_ref,),
        )
        total = len(series)
        for idx, s in enumerate(series, 1):
            _set(phase=i18n.t("sync.phase.episodes", lang).format(kind=conn.kind, idx=idx, total=total))
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
    lang = settings_service.get("general.ui_language")
    cache: dict = {}
    groups, sources = [], []

    # 1) Alle Quellen einlesen (schnell) -----------------------------------
    for conn in connectors:
        _set(phase=i18n.t("sync.phase.reading", lang).format(kind=conn.kind))
        try:
            items = conn.fetch_items()
            existing = {
                r["source_id"]: dict(r)
                for r in db.query("SELECT * FROM media_items WHERE source_ref=?", (conn.source_ref,))
            }
            groups.append((conn, items, existing))
        except Exception as exc:  # noqa: BLE001 - kaputte Quelle stoppt Rest nicht
            sources.append({"kind": conn.kind, "name": conn.source_name,
                            "ok": False, "error": str(exc)})

    total = sum(len(items) for _c, items, _e in groups)
    _set(total=total, processed=0, phase=i18n.t("sync.phase.analyzing", lang))

    # 2) Anreichern (parallel) ---------------------------------------------
    processed = 0
    tvdb_on = bool(providers.api_key_for("tvdb"))
    with ThreadPoolExecutor(max_workers=TMDB_WORKERS) as pool:
        futures = [
            pool.submit(_enrich_one, it, existing, cache, tvdb_on)
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
        _set(phase=i18n.t("sync.phase.saving", lang).format(kind=conn.kind))
        res = db.upsert_items(conn.source_ref, conn.kind, items, now)
        total_seen += res["seen"]
        total_new += len(res["new"])
        sources.append({"kind": conn.kind, "name": conn.source_name, "seen": res["seen"],
                        "new": len(res["new"]), "removed": res["removed"], "ok": True})

    # 4) Episoden je Serie speichern (fuer Sprach-Abdeckung, Staffel-Status) ----
    _sync_episodes([conn for conn, _i, _e in groups], lang)

    # 4b) Vollstaendigkeit je Serie (Staffel 0 zaehlt nicht mit) -----------------
    # Erst jetzt moeglich: die Einzelfolgen liegen in der DB, so laesst sich die
    # HABEN-Seite ohne Specials zaehlen (konsistent zu TMDbs number_of_episodes).
    # 4b0) Episoden-Reihenfolge je Serie bestimmen (Aired/DVD/Absolut) - MUSS vor
    # completeness/seasons laufen, da diese die aufgeloeste Struktur nutzen.
    _set(phase=i18n.t("sync.phase.order", lang))
    episode_order.recompute()
    _set(phase=i18n.t("sync.phase.completeness", lang))
    completeness.recompute()
    # 4c) Ampel je Staffel (Cover-Badges S0/S1/S2 ...) - braucht dieselben
    # Episodendaten, deshalb direkt im Anschluss.
    seasons.recompute()

    # 5) Abdeckung der primaeren Sprache berechnen -------------------------------
    _set(phase=i18n.t("sync.phase.coverage", lang))
    coverage.recompute()

    _set(phase=i18n.t("sync.phase.rules", lang))
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
