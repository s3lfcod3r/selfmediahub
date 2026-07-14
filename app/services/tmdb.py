"""TMDb-Anbindung: deutsche Freigabe, Genres, Staffel-/Episodenzahl, Status.

Alles read-only und best-effort: Fehler brechen den Sync nicht ab.
"""
import requests

from .. import config
from . import providers

BASE = "https://api.themoviedb.org/3"
TIMEOUT = 8
DE_CERTS = {"0", "6", "12", "16", "18"}


def _key() -> str:
    """Effektiver TMDb-Key: aktiver DB-Dienst (Phase 5a), sonst ENV-Fallback."""
    return providers.api_key_for("tmdb") or config.TMDB_API_KEY


def _enabled() -> bool:
    return bool(_key())


def _get(path: str, extra: dict = None):
    params = {"api_key": _key()}
    if extra:
        params.update(extra)
    resp = requests.get(f"{BASE}{path}", params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _resolve_tmdb_id(item: dict, is_series: bool):
    if item.get("tmdb_id"):
        return item["tmdb_id"]
    imdb = item.get("imdb_id")
    if imdb:
        data = _get(f"/find/{imdb}", {"external_source": "imdb_id"})
        results = data.get("tv_results" if is_series else "movie_results", [])
        if results:
            return results[0]["id"]
    # Fallback: Suche nach Name (+ Jahr)
    kind = "tv" if is_series else "movie"
    q = {"query": item.get("name", "")}
    if item.get("year"):
        q["first_air_date_year" if is_series else "year"] = item["year"]
    data = _get(f"/search/{kind}", q)
    results = data.get("results", [])
    return results[0]["id"] if results else None


def _movie_cert(data: dict):
    for entry in data.get("release_dates", {}).get("results", []):
        if entry.get("iso_3166_1") == "DE":
            for rel in entry.get("release_dates", []):
                if rel.get("certification"):
                    return rel["certification"].strip()
    return None


def _tv_cert(data: dict):
    for entry in data.get("content_ratings", {}).get("results", []):
        if entry.get("iso_3166_1") == "DE":
            return (entry.get("rating") or "").strip()
    return None


def compute_missing(seasons: dict, present) -> list:
    """Fehlende Episoden aus {staffel: episodenzahl} vs. vorhandenen (s, e).

    Gibt [] zurück, wenn Embys Nummerierung offensichtlich von TMDb abweicht
    (Anime mit Fake-Staffeln, Absolut-Nummerierung o.Ae.) - dann werden keine
    Einzelfolgen geraten. Staffel 0 (Specials) ist bereits ausgeschlossen.
    """
    if not seasons:
        return []
    present_set = {p for p in present if p[0] is not None and p[1] is not None}
    present_seasons = {s for (s, _e) in present_set}

    # 1) Emby kennt höhere Staffeln als TMDb -> Nummerierung passt nicht.
    if present_seasons and max(present_seasons) > max(seasons):
        return []
    # 2) Viele vorhandene Folgen liegen ausserhalb der TMDb-Struktur.
    expected = {(sn, ep) for sn, cnt in seasons.items() for ep in range(1, cnt + 1)}
    outside = [p for p in present_set if p not in expected]
    if present_set and len(outside) > max(3, 0.2 * len(present_set)):
        return []

    return [{"season": sn, "episode": ep}
            for sn, cnt in sorted(seasons.items())
            for ep in range(1, cnt + 1)
            if (sn, ep) not in present_set]


def tv_season_counts(tmdb_id) -> dict:
    """{Staffel: Episodenzahl} laut TMDb (nur Staffel >= 1). {} bei Fehler/deaktiviert."""
    if not _enabled() or not tmdb_id:
        return {}
    try:
        data = _get(f"/tv/{tmdb_id}")
    except requests.RequestException:
        return {}
    return {
        s["season_number"]: (s.get("episode_count") or 0)
        for s in data.get("seasons", [])
        if s.get("season_number") and s["season_number"] >= 1
    }


def missing_episodes(tmdb_id, present) -> list:
    """Fehlende Episoden ermitteln: TMDb-Staffeln vs. vorhandene (season, episode).

    ``present`` = Iterable aus (season, episode). Best-effort - leere Liste bei
    fehlendem Key/Fehler oder bei abweichender Nummerierung (siehe compute_missing).
    """
    return compute_missing(tv_season_counts(tmdb_id), list(present))


def season_summary(seasons: dict, present) -> dict:
    """Pro-Staffel-Uebersicht 'vorhanden/gesamt laut TMDb'.

    Robust gegen Nummerierungs-Chaos: ``reliable`` wird False, sobald Emby
    Staffeln kennt, die TMDb nicht hat, oder eine Staffel mehr Folgen zeigt,
    als TMDb kennt - dann ist die Staffel-Zuordnung nicht vertrauenswuerdig
    und es sollte stattdessen der allgemeine Hinweis erscheinen.
    """
    if not seasons:
        return {"seasons": [], "reliable": False, "total_tmdb": 0, "total_have": 0}
    present_set = {p for p in present if p[0] is not None and p[1] is not None}
    have_by_season: dict = {}
    for (s, _e) in present_set:
        have_by_season[s] = have_by_season.get(s, 0) + 1
    reliable = not any(s not in seasons for s in have_by_season)
    rows = []
    for sn in sorted(seasons):
        total = seasons[sn]
        have = have_by_season.get(sn, 0)
        if have > total:
            reliable = False
        rows.append({"season": sn, "tmdb_total": total, "have": have})
    return {"seasons": rows, "reliable": reliable,
            "total_tmdb": sum(seasons.values()), "total_have": len(present_set)}


def enrich(item: dict, cache: dict) -> dict:
    """Item mit TMDb-Daten anreichern (in-place). ``cache`` je Sync-Lauf."""
    if not _enabled():
        return item
    is_series = item.get("item_type") == "Serie"
    try:
        tmdb_id = _resolve_tmdb_id(item, is_series)
        if not tmdb_id:
            return item
        item["tmdb_id"] = str(tmdb_id)
        ckey = ("tv" if is_series else "movie", str(tmdb_id))
        data = cache.get(ckey)
        if data is None:
            if is_series:
                data = _get(f"/tv/{tmdb_id}", {"append_to_response": "content_ratings"})
            else:
                data = _get(f"/movie/{tmdb_id}", {"append_to_response": "release_dates"})
            cache[ckey] = data

        # Fill-if-absent: ein hoeher priorisierter Provider (Kette, Phase 5b) hat
        # das Feld ggf. schon gesetzt und darf nicht ueberschrieben werden.
        cert = _tv_cert(data) if is_series else _movie_cert(data)
        if cert in DE_CERTS and not item.get("fsk_suggested"):
            item["fsk_suggested"] = f"DE-{cert}"

        if not item.get("genres"):
            item["genres"] = [g.get("name") for g in data.get("genres", []) if g.get("name")]

        if item.get("status") is None:
            item["status"] = data.get("status")
        if is_series:
            if item.get("tmdb_seasons") is None:
                item["tmdb_seasons"] = data.get("number_of_seasons")
            if item.get("tmdb_episodes") is None:
                item["tmdb_episodes"] = data.get("number_of_episodes")
    except requests.RequestException:
        return item
    return item
