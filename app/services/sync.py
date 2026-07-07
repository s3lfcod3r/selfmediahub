"""Import/Scan-Pipeline: liest alle konfigurierten Quellen, reichert an, speichert."""
from datetime import datetime, timezone

from .. import config, db
from ..connectors.emby import EmbyConnector
from ..connectors.jellyfin import JellyfinConnector
from ..connectors.local import LocalConnector
from ..connectors.plex import PlexConnector
from . import analysis, completeness, fsk, notify, rules, tmdb


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


def _enrich(item: dict, cache: dict) -> None:
    analysis.enrich(item)
    tmdb.enrich(item, cache)
    completeness.compute(item)
    fsk.analyze(item)


def run_sync() -> dict:
    """Vollen Re-Sync aller Quellen ausfuehren."""
    connectors = build_connectors()
    if not connectors:
        raise RuntimeError("Keine Medienquelle konfiguriert.")

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cache: dict = {}
    total, total_new, sources = 0, 0, []

    for conn in connectors:
        try:
            items = conn.fetch_items()
            for it in items:
                _enrich(it, cache)
            res = db.upsert_items(conn.kind, items, now)
            total += res["seen"]
            total_new += len(res["new"])
            sources.append({
                "kind": conn.kind, "seen": res["seen"],
                "new": len(res["new"]), "removed": res["removed"], "ok": True,
            })
        except Exception as exc:  # noqa: BLE001 - eine kaputte Quelle stoppt nicht den Rest
            sources.append({"kind": conn.kind, "ok": False, "error": str(exc)})

    rule_res = rules.apply_all()
    db.set_meta("last_sync", now)
    db.set_meta("last_sync_count", str(total))

    if total_new:
        notify.send("new_items", f"{total_new} neue Eintraege in der Mediathek", {"count": total_new})

    return {"count": total, "new": total_new, "at": now,
            "sources": sources, "rules": rule_res}
