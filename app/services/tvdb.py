"""TheTVDB-Provider (v4). Ergaenzt vor allem Episoden-/Staffelzahlen fuer Serien
und Anime, wo TMDbs Nummerierung oft abweicht.

Alles best-effort: jeder Fehler faellt still auf den naechsten Provider der Kette
zurueck (i.d.R. TMDb). Felder werden nur gesetzt, wenn sie noch leer sind
(fill-if-absent) - so gewinnt der hoechstpriorisierte Dienst je Feld.
"""
import json
import statistics
import threading
import time

import requests

from . import providers

BASE = "https://api4.thetvdb.com/v4"
TIMEOUT = 8
_MAX_EPISODE_PAGES = 20  # Sicherheitskappe gegen Endlos-Pagination

# Unsere Reihenfolgen-Keys -> TheTVDB-season-type-Endpunkt.
# 'default' = Aired-Reihenfolge, 'dvd'/'absolute' analog.
_SEASONTYPE = {"aired": "default", "dvd": "dvd", "absolute": "absolute"}

# Login-Token cachen (TheTVDB-Token gilt ~1 Monat); konservativ 20 Tage.
_lock = threading.Lock()
_token = {"key": None, "value": None, "exp": 0.0}
_TOKEN_TTL = 20 * 24 * 3600


def _login(api_key: str) -> str:
    resp = requests.post(f"{BASE}/login", json={"apikey": api_key}, timeout=TIMEOUT)
    resp.raise_for_status()
    return (resp.json().get("data") or {}).get("token") or ""


def key_ok() -> tuple:
    """Testabfrage fuer die Rotations-Kontrolle: prueft per Login, ob der
    effektive TheTVDB-Key noch gueltig ist. Gibt (ok, meldung) zurueck."""
    key = providers.api_key_for("tvdb")
    if not key:
        return False, "kein Key"
    try:
        token = _login(key)
        return (bool(token), "ok" if token else "kein Token")
    except requests.RequestException as exc:
        return False, str(exc)


def _get_token(api_key: str) -> str:
    now = time.time()
    with _lock:
        if _token["value"] and _token["key"] == api_key and _token["exp"] > now:
            return _token["value"]
    tok = _login(api_key)  # Netzabruf ausserhalb des Locks
    with _lock:
        _token.update(key=api_key, value=tok, exp=now + _TOKEN_TTL)
    return tok


def _get(path: str, token: str, params: dict = None) -> dict:
    resp = requests.get(f"{BASE}{path}", params=params,
                        headers={"Authorization": f"Bearer {token}"}, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json() or {}


def _external_ids(item: dict) -> dict:
    try:
        ids = json.loads(item.get("external_ids") or "{}")
        return ids if isinstance(ids, dict) else {}
    except (ValueError, TypeError):
        return {}


def _resolve_series_id(item: dict, token: str):
    ids = _external_ids(item)
    if ids.get("tvdb"):
        return ids["tvdb"]
    name = (item.get("name") or "").strip()
    if not name:
        return None
    res = _get("/search", token, {"query": name, "type": "series"}).get("data") or []
    if res:
        return res[0].get("tvdb_id") or res[0].get("id")
    return None


def _remember_id(item: dict, series_id) -> None:
    """Per Suche gefundene tvdb-ID in external_ids ergaenzen (fuer den naechsten Sync)."""
    ids = _external_ids(item)
    if not ids.get("tvdb"):
        ids["tvdb"] = str(series_id)
        item["external_ids"] = json.dumps(ids)


def _available_orders(ext: dict) -> list:
    """Verfuegbare Reihenfolgen laut TheTVDB-Staffeltypen. 'aired' immer dabei;
    'dvd'/'absolute' nur, wenn TheTVDB fuer die Serie so eine Nummerierung kennt."""
    types = {(s.get("type") or {}).get("type") for s in (ext.get("seasons") or [])}
    orders = ["aired"]
    if "dvd" in types:
        orders.append("dvd")
    if "absolute" in types:
        orders.append("absolute")
    return orders


def _fetch_order(series_id, token: str, order: str, cache: dict):
    """Eine Reihenfolge abrufen -> {season_counts, episodes, seasons, runtime} oder
    None. Zaehlt nur regulaere Staffeln (>= 1); runtime = Median der Folgen-Laufzeit
    (Entscheidungsgrundlage fuer die Aired/DVD-Vorwahl)."""
    ck = ("tvdb_order", str(series_id), order)
    if ck in cache:
        return cache[ck]
    counts: dict = {}
    runtimes: list = []
    page, pages = 0, 0
    while pages < _MAX_EPISODE_PAGES:
        try:
            j = _get(f"/series/{series_id}/episodes/{_SEASONTYPE[order]}", token, {"page": page})
        except requests.RequestException:
            break
        data = j.get("data") or {}
        eps = data.get("episodes") or []
        if not eps:
            break
        for ep in eps:
            sn = ep.get("seasonNumber")
            if sn is None or sn < 1:  # Staffel 0 (Specials) zaehlt nicht
                continue
            counts[sn] = counts.get(sn, 0) + 1
            rt = ep.get("runtime")
            if rt:
                runtimes.append(rt)
        pages += 1
        if not (j.get("links") or {}).get("next"):
            break
        page += 1
    if not counts:
        cache[ck] = None
        return None
    result = {
        "season_counts": sorted([s, c] for s, c in counts.items()),
        "episodes": sum(counts.values()),
        "seasons": len(counts),
        "runtime": round(statistics.median(runtimes)) if runtimes else None,
    }
    cache[ck] = result
    return result


def enrich(item: dict, cache: dict) -> dict:
    """Serie/Anime ueber TheTVDB anreichern (fill-if-absent). Filme werden hier
    nicht behandelt (TMDb bleibt dafuer zustaendig)."""
    if item.get("item_type") != "Serie":
        return item
    key = providers.api_key_for("tvdb")
    if not key:
        return item
    try:
        token = _get_token(key)
        if not token:
            return item
        series_id = _resolve_series_id(item, token)
        if not series_id:
            return item
        ext = _get(f"/series/{series_id}/extended", token).get("data") or {}

        if not item.get("genres"):
            genres = [g.get("name") for g in (ext.get("genres") or []) if g.get("name")]
            if genres:
                item["genres"] = genres

        if item.get("status") is None:
            status = (ext.get("status") or {}).get("name")
            if status:
                item["status"] = status

        # Alle bei TheTVDB vorhandenen Reihenfolgen abrufen (Aired immer, DVD/
        # Absolut wenn vorhanden). episode_order.recompute() waehlt spaeter anhand
        # der tatsaechlichen Folgen-Laufzeit die passende aus.
        orders_out = {}
        for order in _available_orders(ext):
            res = _fetch_order(series_id, token, order, cache)
            if res:
                orders_out[order] = res
        if orders_out:
            item["tvdb_orders"] = orders_out
            aired = orders_out.get("aired")
            if aired:  # Aired bleibt die Basis fuer tmdb_seasons/tmdb_episodes.
                if item.get("tmdb_seasons") is None:
                    item["tmdb_seasons"] = aired["seasons"]
                if item.get("tmdb_episodes") is None:
                    item["tmdb_episodes"] = aired["episodes"]

        _remember_id(item, series_id)
    except requests.RequestException:
        return item
    return item
