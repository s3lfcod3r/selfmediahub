"""TMDb-Anbindung: deutsche Freigabe, Genres, Staffel-/Episodenzahl, Status.

Alles read-only und best-effort: Fehler brechen den Sync nicht ab.
"""
import requests

from .. import config

BASE = "https://api.themoviedb.org/3"
TIMEOUT = 8
DE_CERTS = {"0", "6", "12", "16", "18"}


def _get(path: str, extra: dict = None):
    params = {"api_key": config.TMDB_API_KEY}
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


def enrich(item: dict, cache: dict) -> dict:
    """Item mit TMDb-Daten anreichern (in-place). ``cache`` je Sync-Lauf."""
    if not config.tmdb_enabled():
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

        cert = _tv_cert(data) if is_series else _movie_cert(data)
        if cert in DE_CERTS:
            item["fsk_suggested"] = f"DE-{cert}"

        if not item.get("genres"):
            item["genres"] = [g.get("name") for g in data.get("genres", []) if g.get("name")]

        if is_series:
            item["tmdb_seasons"] = data.get("number_of_seasons")
            item["tmdb_episodes"] = data.get("number_of_episodes")
            item["status"] = data.get("status")
        else:
            item["status"] = data.get("status")
    except requests.RequestException:
        return item
    return item
