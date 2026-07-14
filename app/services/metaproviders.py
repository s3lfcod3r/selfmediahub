"""Metadaten-Anreicherung ueber mehrere Provider (Phase 5b).

Bestimmt die Medienart (film/serie/anime) und laeuft die fuer diese Medienart
konfigurierte Prioritaetskette durch (siehe ``providers.chain_kinds``). Jeder
Provider fuellt nur noch leere Felder (fill-if-absent) -> der hoechstpriorisierte
Dienst gewinnt je Feld. Beispiel: 'AniDB/TheTVDB zuerst fuer Anime'.

Anime-Erkennung per Genre (Emby-Daten): Genre 'Anime', oder 'Animation' mit
japanischem Ton/Untertitel als Zusatzsignal.
"""
import json

from . import providers, tmdb, tvdb

_ENRICHERS = {"tmdb": tmdb.enrich, "tvdb": tvdb.enrich}
_ANIME_GENRES = {"anime"}
_ANIMATION_GENRES = {"animation", "animationsfilm"}
_JAPANESE = {"ja", "jp", "jpn", "jpa"}


def _as_list(value) -> list:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            return []
    return value if isinstance(value, list) else []


def _has_japanese(item: dict) -> bool:
    for field in ("audio_langs", "subtitle_langs"):
        for lang in _as_list(item.get(field)):
            code = str(lang).lower()
            if code[:2] in _JAPANESE or code[:3] in _JAPANESE:
                return True
    return False


def _media_type(item: dict) -> str:
    if item.get("item_type") != "Serie":
        return "film"
    genres = {str(g).lower() for g in _as_list(item.get("genres"))}
    if genres & _ANIME_GENRES:
        return "anime"
    if (genres & _ANIMATION_GENRES) and _has_japanese(item):
        return "anime"
    return "serie"


def enrich_item(item: dict, cache: dict) -> dict:
    """Item ueber die Provider-Kette seiner Medienart anreichern (in-place)."""
    media_type = _media_type(item)
    for kind in providers.chain_kinds(media_type):
        enrich = _ENRICHERS.get(kind)
        if not enrich:
            continue
        try:
            enrich(item, cache)
        except Exception:  # noqa: BLE001 - ein Provider darf die Kette nicht kippen
            # Best-effort: naechster Provider (z.B. TMDb) bekommt trotzdem seine Chance.
            pass
    return item
