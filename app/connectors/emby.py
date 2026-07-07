"""Emby-Connector - liest Filme und Serien ausschliesslich ueber die Emby-API.

Jellyfin erbt hiervon (fast identische API), siehe jellyfin.py.
"""
import requests

from .base import Connector

TIMEOUT = 60
IMAGE_MAX_HEIGHT = 450
TICKS_PER_MINUTE = 600_000_000
ITEM_FIELDS = (
    "OfficialRating,ProductionYear,Genres,CommunityRating,ChildCount,"
    "RecursiveItemCount,Overview,SortName,ProviderIds,MediaSources,RunTimeTicks"
)
LIBRARY_TYPES = ("movies", "tvshows", "mixed")


def _dedupe(seq):
    out = []
    for v in seq:
        if v and v not in out:
            out.append(v)
    return out


def _resolution_label(height):
    h = height or 0
    if h >= 2000:
        return "4K"
    if h >= 1000:
        return "1080p"
    if h >= 700:
        return "720p"
    if h >= 570:
        return "576p"
    if h >= 400:
        return "480p"
    return "SD" if h > 0 else None


def tech_from_streams(streams: list) -> dict:
    """Technische Merkmale aus Emby/Jellyfin-MediaStreams ziehen."""
    video_codec = width = height = hdr = None
    audio_codecs, audio_langs, subtitle_langs = [], [], []
    for st in streams or []:
        stype = st.get("Type")
        if stype == "Video" and video_codec is None:
            video_codec = st.get("Codec")
            width, height = st.get("Width"), st.get("Height")
            hdr = st.get("VideoRangeType") or st.get("VideoRange")
        elif stype == "Audio":
            audio_codecs.append(st.get("Codec"))
            audio_langs.append(st.get("Language"))
        elif stype == "Subtitle":
            subtitle_langs.append(st.get("Language"))
    return {
        "video_codec": video_codec, "width": width, "height": height,
        "hdr": hdr,
        "audio_codecs": _dedupe(audio_codecs),
        "audio_langs": _dedupe(audio_langs),
        "subtitle_langs": _dedupe(subtitle_langs),
    }


class EmbyConnector(Connector):
    kind = "emby"
    prefix = "/emby"

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._admin_id = None

    # -- HTTP ---------------------------------------------------------------
    def _headers(self) -> dict:
        return {"X-Emby-Token": self.api_key}

    def _get(self, path: str, params: dict = None):
        resp = requests.get(
            f"{self.base_url}{self.prefix}{path}",
            headers=self._headers(), params=params, timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    def _admin_user_id(self) -> str:
        if self._admin_id:
            return self._admin_id
        for user in self._get("/Users"):
            if user.get("Policy", {}).get("IsAdministrator"):
                self._admin_id = user["Id"]
                return self._admin_id
        raise RuntimeError(f"Kein Admin-Benutzer in {self.kind} gefunden")

    # -- Schnittstelle ------------------------------------------------------
    def test_connection(self) -> None:
        self._get("/System/Info")

    def fetch_items(self) -> list:
        uid = self._admin_user_id()
        items = []
        for view in self._libraries(uid):
            items.extend(self._fetch_view(uid, view))
        return items

    # -- Detailschritte -----------------------------------------------------
    def _libraries(self, uid: str) -> list:
        data = self._get(f"/Users/{uid}/Views")
        return [v for v in data.get("Items", [])
                if v.get("CollectionType") in LIBRARY_TYPES]

    def _fetch_view(self, uid: str, view: dict) -> list:
        params = {
            "Recursive": "true",
            "IncludeItemTypes": "Movie,Series",
            "Fields": ITEM_FIELDS,
            "ParentId": view["Id"],
            "EnableImages": "false",
        }
        data = self._get(f"/Users/{uid}/Items", params)
        library_name = view.get("Name", "")
        return [self._normalize(it, library_name) for it in data.get("Items", [])]

    def _image_url(self, item_id: str) -> str:
        return (
            f"{self.base_url}{self.prefix}/Items/{item_id}/Images/Primary"
            f"?maxHeight={IMAGE_MAX_HEIGHT}&api_key={self.api_key}"
        )

    def _normalize(self, it: dict, library_name: str) -> dict:
        item_id = it["Id"]
        is_series = it.get("Type") == "Series"
        providers = it.get("ProviderIds") or {}
        ticks = it.get("RunTimeTicks")
        item = {
            "source_id": item_id,
            "item_type": "Serie" if is_series else "Film",
            "name": it.get("Name", ""),
            "sort_name": it.get("SortName") or it.get("Name", ""),
            "year": it.get("ProductionYear"),
            "official_rating": it.get("OfficialRating") or "",
            "community_rating": it.get("CommunityRating"),
            "genres": it.get("Genres") or [],
            "image_url": self._image_url(item_id),
            "library_name": library_name,
            "child_count": it.get("ChildCount"),
            "overview": it.get("Overview") or "",
            "tmdb_id": providers.get("Tmdb") or providers.get("tmdb"),
            "imdb_id": providers.get("Imdb") or providers.get("imdb"),
            "runtime_min": round(ticks / TICKS_PER_MINUTE) if ticks else None,
        }
        if is_series:
            item["have_seasons"] = it.get("ChildCount")
            item["have_episodes"] = it.get("RecursiveItemCount")
        else:
            sources = it.get("MediaSources") or []
            streams = sources[0].get("MediaStreams") if sources else []
            item.update(tech_from_streams(streams))
            if sources:
                item["size_bytes"] = sources[0].get("Size")
        return item

    def fetch_episodes(self, series_id: str) -> list:
        """Alle Episoden einer Serie mit Technik holen (live, read-only)."""
        uid = self._admin_user_id()
        params = {
            "Recursive": "true",
            "IncludeItemTypes": "Episode",
            "ParentId": series_id,
            "Fields": "MediaSources,RunTimeTicks,Overview",
            "EnableImages": "false",
        }
        data = self._get(f"/Users/{uid}/Items", params)
        episodes = []
        for it in data.get("Items", []):
            sources = it.get("MediaSources") or []
            streams = sources[0].get("MediaStreams") if sources else []
            ticks = it.get("RunTimeTicks")
            ep = {
                "season": it.get("ParentIndexNumber"),
                "episode": it.get("IndexNumber"),
                "name": it.get("Name", ""),
                "size_bytes": sources[0].get("Size") if sources else None,
                "runtime_min": round(ticks / TICKS_PER_MINUTE) if ticks else None,
            }
            ep.update(tech_from_streams(streams))
            ep["resolution"] = _resolution_label(ep.get("height"))
            episodes.append(ep)
        episodes.sort(key=lambda e: ((e["season"] if e["season"] is not None else 999),
                                     (e["episode"] if e["episode"] is not None else 999)))
        return episodes
