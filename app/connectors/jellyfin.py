"""Jellyfin-Connector. Jellyfin ist ein Emby-Fork mit fast identischer API -
Hauptunterschied: kein ``/emby``-Prefix. Alles andere erbt von EmbyConnector.
"""
from .emby import EmbyConnector


class JellyfinConnector(EmbyConnector):
    kind = "jellyfin"
    prefix = ""
