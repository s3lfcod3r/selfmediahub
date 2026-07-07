"""Emby-Connector - liest Filme und Serien ausschliesslich ueber die Emby-API."""
import requests

from .base import Connector

TIMEOUT = 60
IMAGE_MAX_HEIGHT = 450
ITEM_FIELDS = (
    "OfficialRating,ProductionYear,Genres,CommunityRating,"
    "ChildCount,Overview,SortName"
)
LIBRARY_TYPES = ("movies", "tvshows", "mixed")


class EmbyConnector(Connector):
    kind = "emby"

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._admin_id = None

    # -- interne HTTP-Helfer ------------------------------------------------
    def _headers(self) -> dict:
        return {"X-Emby-Token": self.api_key}

    def _get(self, path: str, params: dict = None):
        resp = requests.get(
            f"{self.base_url}{path}",
            headers=self._headers(),
            params=params,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    def _admin_user_id(self) -> str:
        if self._admin_id:
            return self._admin_id
        for user in self._get("/emby/Users"):
            if user.get("Policy", {}).get("IsAdministrator"):
                self._admin_id = user["Id"]
                return self._admin_id
        raise RuntimeError("Kein Admin-Benutzer in Emby gefunden")

    # -- oeffentliche Schnittstelle ----------------------------------------
    def test_connection(self) -> None:
        self._get("/emby/System/Info")

    def fetch_items(self) -> list:
        uid = self._admin_user_id()
        items = []
        for view in self._libraries(uid):
            items.extend(self._fetch_view(uid, view))
        return items

    # -- Detailschritte -----------------------------------------------------
    def _libraries(self, uid: str) -> list:
        """Nur Film-/Serien-Bibliotheken (Views) zurueckgeben."""
        data = self._get(f"/emby/Users/{uid}/Views")
        return [
            v for v in data.get("Items", [])
            if v.get("CollectionType") in LIBRARY_TYPES
        ]

    def _fetch_view(self, uid: str, view: dict) -> list:
        params = {
            "Recursive": "true",
            "IncludeItemTypes": "Movie,Series",
            "Fields": ITEM_FIELDS,
            "ParentId": view["Id"],
            "EnableImages": "false",
        }
        data = self._get(f"/emby/Users/{uid}/Items", params)
        library_name = view.get("Name", "")
        return [self._normalize(it, library_name) for it in data.get("Items", [])]

    def _normalize(self, it: dict, library_name: str) -> dict:
        item_id = it["Id"]
        is_series = it.get("Type") == "Series"
        image_url = (
            f"{self.base_url}/emby/Items/{item_id}/Images/Primary"
            f"?maxHeight={IMAGE_MAX_HEIGHT}&api_key={self.api_key}"
        )
        return {
            "source_id": item_id,
            "item_type": "Serie" if is_series else "Film",
            "name": it.get("Name", ""),
            "sort_name": it.get("SortName") or it.get("Name", ""),
            "year": it.get("ProductionYear"),
            "official_rating": it.get("OfficialRating") or "",
            "community_rating": it.get("CommunityRating"),
            "genres": it.get("Genres") or [],
            "image_url": image_url,
            "library_name": library_name,
            "child_count": it.get("ChildCount"),
            "overview": it.get("Overview") or "",
        }
