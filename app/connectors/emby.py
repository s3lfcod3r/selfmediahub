"""Emby-Connector - liest Filme und Serien ausschließlich über die Emby-API.

Jellyfin erbt hiervon (fast identische API), siehe jellyfin.py.
"""
import json
from concurrent.futures import ThreadPoolExecutor

import requests

from .base import Connector

# Sperr-Status je Item einzeln lesen: der Listen-Endpoint liefert LockedFields/
# LockData nicht (Emby-Eigenheit) - siehe fetch_rating_locks(). Parallelitaet,
# damit der On-Demand-Refresh auch bei grossen Bibliotheken zuegig bleibt.
LOCK_FETCH_WORKERS = 8

TIMEOUT = 60
IMAGE_MAX_HEIGHT = 450
TICKS_PER_MINUTE = 600_000_000
ITEM_FIELDS = (
    "OfficialRating,ProductionYear,Genres,CommunityRating,ChildCount,"
    "RecursiveItemCount,Overview,SortName,ProviderIds,MediaSources,RunTimeTicks,Path,LockedFields"
)
LIBRARY_TYPES = ("movies", "tvshows", "mixed")


def _rating_locked(it: dict) -> int:
    """OfficialRating in Emby gesperrt? Ganzes Item (``LockData``) oder feldweise
    (``OfficialRating`` in ``LockedFields``). ACHTUNG: Beide Felder liefert nur das
    Einzel-Item-Objekt - im Listen-DTO fehlen sie (Emby serialisiert sie dort nicht)."""
    return 1 if (it.get("LockData")
                 or "OfficialRating" in (it.get("LockedFields") or [])) else 0


def _dedupe(seq):
    out = []
    for v in seq:
        if v and v not in out:
            out.append(v)
    return out


def _resolution_label(width, height):
    w, h = width or 0, height or 0
    if w >= 3800 or h >= 2000:
        return "4K"
    return f"{h}p" if h > 0 else None


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

    def __init__(self, base_url: str, api_key: str, libraries=None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        # Ausgewaehlte Bibliotheks-IDs (leer/None = alle ueberwachen).
        self.libraries = {str(x) for x in libraries} if libraries else None
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
    def _all_views(self, uid: str) -> list:
        """Alle Film-/Serien-Bibliotheken (ohne Auswahl-Filter)."""
        data = self._get(f"/Users/{uid}/Views")
        return [v for v in data.get("Items", [])
                if v.get("CollectionType") in LIBRARY_TYPES]

    def _libraries(self, uid: str) -> list:
        views = self._all_views(uid)
        if self.libraries:
            views = [v for v in views if str(v.get("Id")) in self.libraries]
        return views

    def list_libraries(self) -> list:
        """Verfuegbare Bibliotheken [{id, name}] fuer die UI-Auswahl."""
        uid = self._admin_user_id()
        return [{"id": str(v.get("Id")), "name": v.get("Name", "")}
                for v in self._all_views(uid)]

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
        # Alle externen IDs generisch merken (Basis fuer Multi-Provider, Phase 5).
        # Schluessel klein geschrieben: tmdb, imdb, tvdb, anidb ...
        ids = {k.lower(): str(v) for k, v in providers.items() if v}
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
            "path": it.get("Path") or "",
            "tmdb_id": ids.get("tmdb"),
            "imdb_id": ids.get("imdb"),
            "external_ids": json.dumps(ids),
            # Freigabe in Emby gesperrt? Im Listen-Sync fast immer 0, weil der
            # Listen-Endpoint LockedFields/LockData nicht liefert - der echte
            # Stand kommt ueber fetch_rating_locks() (FSK-Seite: "Sperren pruefen").
            "rating_locked": _rating_locked(it),
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
            "Fields": "MediaSources,RunTimeTicks,Overview,Path",
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
                "path": it.get("Path") or "",
                "size_bytes": sources[0].get("Size") if sources else None,
                "runtime_min": round(ticks / TICKS_PER_MINUTE) if ticks else None,
            }
            ep.update(tech_from_streams(streams))
            ep["resolution"] = _resolution_label(ep.get("width"), ep.get("height"))
            episodes.append(ep)
        episodes.sort(key=lambda e: ((e["season"] if e["season"] is not None else 999),
                                     (e["episode"] if e["episode"] is not None else 999)))
        return episodes

    def fetch_rating_locks(self, source_ids: list) -> dict:
        """Sperr-Status (rating_locked) je Item frisch aus der Quelle lesen.

        Noetig, weil der Listen-Endpoint ``LockedFields``/``LockData`` NICHT
        serialisiert (auch nicht via ``Fields``) - nur das Einzel-Item-Objekt
        ``/Users/{uid}/Items/{id}`` enthaelt sie. Read-only; parallelisiert.

        Rueckgabe ``{source_id: 0|1|None}``. ``None`` = Item nicht lesbar; der
        Aufrufer soll den vorhandenen DB-Wert dann NICHT ueberschreiben.
        """
        if not source_ids:
            return {}
        uid = self._admin_user_id()
        headers = self._headers()
        base = f"{self.base_url}{self.prefix}/Users/{uid}/Items/"

        def _one(sid):
            try:
                resp = requests.get(f"{base}{sid}", headers=headers, timeout=TIMEOUT)
                resp.raise_for_status()
                return sid, _rating_locked(resp.json())
            except (requests.RequestException, ValueError):
                return sid, None

        with ThreadPoolExecutor(max_workers=LOCK_FETCH_WORKERS) as pool:
            return dict(pool.map(_one, source_ids))
