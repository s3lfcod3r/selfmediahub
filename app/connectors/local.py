"""Lokaler-Ordner-Connector - katalogisiert Videodateien anhand ihrer Namen.

Bewusst leichtgewichtig: parst Titel/Jahr und SxxExx, gruppiert Episoden zu
Serien und zaehlt Staffeln/Episoden. Tiefe Technik-Analyse (Codec/Aufloesung)
braucht ffprobe und folgt spaeter.
"""
import os
import re

from .base import Connector

VIDEO_EXTS = {".mkv", ".mp4", ".avi", ".m4v", ".mov", ".wmv", ".ts", ".m2ts"}
_EPISODE_RE = re.compile(r"^(?P<show>.+?)[._ -]+[Ss](?P<s>\d{1,2})[Ee](?P<e>\d{1,3})")
_MOVIE_RE = re.compile(r"^(?P<title>.+?)[._ (\[]+(?P<year>19\d{2}|20\d{2})")


def _clean(name: str) -> str:
    return re.sub(r"[._]+", " ", name).strip(" -_[](){}")


class LocalConnector(Connector):
    kind = "local"

    def __init__(self, paths: list):
        self.paths = paths

    def test_connection(self) -> None:
        missing = [p for p in self.paths if not os.path.isdir(p)]
        if missing:
            raise RuntimeError("Pfad nicht gefunden: " + ", ".join(missing))

    def fetch_items(self) -> list:
        movies, series = {}, {}
        for root in self.paths:
            for dirpath, _dirs, files in os.walk(root):
                for fname in files:
                    ext = os.path.splitext(fname)[1].lower()
                    if ext not in VIDEO_EXTS:
                        continue
                    self._classify(dirpath, fname, movies, series)
        items = list(movies.values())
        items.extend(self._series_items(series))
        return items

    def _classify(self, dirpath, fname, movies, series):
        stem = os.path.splitext(fname)[0]
        ep = _EPISODE_RE.match(stem)
        if ep:
            show = _clean(ep.group("show")) or os.path.basename(dirpath)
            bucket = series.setdefault(show, {"seasons": set(), "eps": 0})
            bucket["seasons"].add(int(ep.group("s")))
            bucket["eps"] += 1
            return
        mv = _MOVIE_RE.match(stem)
        title = _clean(mv.group("title")) if mv else _clean(stem)
        year = int(mv.group("year")) if mv else None
        path = os.path.join(dirpath, fname)
        movies[path] = {
            "source_id": "movie:" + path,
            "item_type": "Film",
            "name": title,
            "sort_name": title,
            "year": year,
            "path": path,
            "official_rating": "",
            "genres": [],
            "image_url": "",
            "library_name": "Lokal",
            "overview": "",
        }

    def _series_items(self, series: dict) -> list:
        out = []
        for show, info in series.items():
            out.append({
                "source_id": "series:" + show.lower(),
                "item_type": "Serie",
                "name": show,
                "sort_name": show,
                "official_rating": "",
                "genres": [],
                "image_url": "",
                "library_name": "Lokal",
                "overview": "",
                "have_seasons": len(info["seasons"]),
                "have_episodes": info["eps"],
                "child_count": len(info["seasons"]),
            })
        return out
