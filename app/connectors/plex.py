"""Plex-Connector - liest Filme und Serien nur lesend ueber die Plex-API (JSON)."""
import requests

from .base import Connector

TIMEOUT = 60


def _guids(meta: dict) -> dict:
    """tmdb/imdb-IDs aus Plex-Guid-Liste ('tmdb://123', 'imdb://tt..')."""
    out = {}
    for g in meta.get("Guid") or []:
        gid = g.get("id", "")
        if gid.startswith("tmdb://"):
            out["tmdb"] = gid.split("://", 1)[1]
        elif gid.startswith("imdb://"):
            out["imdb"] = gid.split("://", 1)[1]
    return out


class PlexConnector(Connector):
    kind = "plex"

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _get(self, path: str, params: dict = None):
        params = dict(params or {})
        params["X-Plex-Token"] = self.token
        resp = requests.get(
            f"{self.base_url}{path}", params=params,
            headers={"Accept": "application/json"}, timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("MediaContainer", {})

    def test_connection(self) -> None:
        self._get("/identity")

    def fetch_items(self) -> list:
        items = []
        for sec in self._get("/library/sections").get("Directory", []):
            if sec.get("type") in ("movie", "show"):
                items.extend(self._fetch_section(sec))
        return items

    def _fetch_section(self, sec: dict) -> list:
        data = self._get(f"/library/sections/{sec['key']}/all")
        lib = sec.get("title", "")
        return [self._normalize(m, lib) for m in data.get("Metadata", [])]

    def _image_url(self, meta: dict) -> str:
        thumb = meta.get("thumb")
        if not thumb:
            return ""
        return f"{self.base_url}{thumb}?X-Plex-Token={self.token}"

    def _normalize(self, meta: dict, library_name: str) -> dict:
        is_series = meta.get("type") == "show"
        ids = _guids(meta)
        genres = [g.get("tag") for g in meta.get("Genre") or [] if g.get("tag")]
        item = {
            "source_id": str(meta.get("ratingKey")),
            "item_type": "Serie" if is_series else "Film",
            "name": meta.get("title", ""),
            "sort_name": meta.get("titleSort") or meta.get("title", ""),
            "year": meta.get("year"),
            "official_rating": meta.get("contentRating") or "",
            "community_rating": meta.get("rating"),
            "genres": genres,
            "image_url": self._image_url(meta),
            "library_name": library_name,
            "overview": meta.get("summary") or "",
            "tmdb_id": ids.get("tmdb"),
            "imdb_id": ids.get("imdb"),
        }
        dur = meta.get("duration")
        item["runtime_min"] = round(dur / 60000) if dur else None
        if is_series:
            item["have_seasons"] = meta.get("childCount")
            item["have_episodes"] = meta.get("leafCount")
            item["child_count"] = meta.get("childCount")
        else:
            media = meta.get("Media") or []
            if media:
                item["video_codec"] = media[0].get("videoCodec")
                item["width"] = media[0].get("width")
                item["height"] = media[0].get("height")
                parts = media[0].get("Part") or []
                if parts:
                    item["size_bytes"] = parts[0].get("size")
                    item["path"] = parts[0].get("file") or ""
        return item

    def _res(self, w, h):
        w, h = w or 0, h or 0
        if w >= 3800 or h >= 2000:
            return "4K"
        return f"{h}p" if h > 0 else None

    def fetch_episodes(self, series_id: str) -> list:
        """Alle Episoden einer Serie (live, read-only)."""
        data = self._get(f"/library/metadata/{series_id}/allLeaves")
        episodes = []
        for m in data.get("Metadata", []):
            media = m.get("Media") or []
            v = media[0] if media else {}
            parts = v.get("Part") or []
            dur = m.get("duration")
            episodes.append({
                "season": m.get("parentIndex"),
                "episode": m.get("index"),
                "name": m.get("title", ""),
                "video_codec": v.get("videoCodec"),
                "height": v.get("height"),
                "resolution": self._res(v.get("width"), v.get("height")),
                "size_bytes": parts[0].get("size") if parts else None,
                "runtime_min": round(dur / 60000) if dur else None,
                "audio_langs": [], "subtitle_langs": [],
            })
        episodes.sort(key=lambda e: ((e["season"] if e["season"] is not None else 999),
                                     (e["episode"] if e["episode"] is not None else 999)))
        return episodes
