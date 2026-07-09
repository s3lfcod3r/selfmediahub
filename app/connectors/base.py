"""Gemeinsame Schnittstelle aller Connectoren.

Ein Connector liest eine fremde Mediathek und liefert *normalisierte* Items.
So kommen später Plex/Jellyfin/lokale Ordner dazu, ohne den Rest zu ändern.

Normalisiertes Item (dict):
    source_id, item_type ("Film"|"Serie"), name, sort_name, year,
    official_rating, community_rating, genres (list[str]),
    image_url, library_name, child_count, overview
"""
from abc import ABC, abstractmethod


class Connector(ABC):
    kind = "base"

    @abstractmethod
    def test_connection(self) -> None:
        """Verbindung prüfen. Wirft bei Fehler eine Exception."""

    @abstractmethod
    def fetch_items(self) -> list:
        """Alle Filme + Serien als normalisierte Item-Dicts zurückgeben."""
