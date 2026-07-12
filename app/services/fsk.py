"""FSK-Qualitätskontrolle (aus emby-fsk-manager portiert).

- analyze(): read-only. Prüft Freigabe auf Plausibilität, nutzt TMDb-Vorschlag.
- write_emby(): AUSNAHME - schreibt eine Freigabe aktiv nach Emby zurück.
  Nur wenn ALLOW_EMBY_WRITE=1. SelfMediaHub ist sonst strikt read-only.
"""
import json

import requests

from .. import config

VALID_RATINGS = ["DE-0", "DE-6", "DE-12", "DE-16", "DE-18",
                 "FSK-0", "FSK-6", "FSK-12", "FSK-16", "FSK-18"]
FAMILY_GENRES = {"Animation", "Familie", "Family", "Kids", "Kinder", "Komoedie", "Komödie", "Comedy"}
MATURE_GENRES = {"Horror", "Krieg", "War", "Thriller", "Krimi", "Crime"}
RATING_AGE = {
    "G": 0, "TV-G": 0, "TV-Y": 0, "TV-Y7": 6, "U": 0, "ATP": 0, "L": 0, "K": 0,
    "0": 0, "0+": 0, "C": 0,
    "PG": 6, "6": 6, "6+": 6, "7": 6, "TV-PG": 6,
    "PG-13": 12, "12": 12, "12+": 12, "14": 12, "14+": 12, "TV-14": 12, "M12": 12, "UA13+": 12,
    "16": 16, "16+": 16, "M16": 16, "MA15+": 16, "-16": 16,
    "R": 16, "TV-MA": 16, "NC-17": 18, "18": 18, "18+": 18, "+18": 18, "M18": 18, "ES-18": 18,
}


def _age_of(rating: str):
    if not rating:
        return None
    rating = rating.strip()
    if rating in VALID_RATINGS:
        return int(rating.split("-")[1])
    return RATING_AGE.get(rating)


def plausibility(official: str, suggested: str, genres: list):
    """Gibt (suspicious, reason). Nutzt vorhandene oder vorgeschlagene Freigabe."""
    rating = official or suggested
    age = _age_of(rating)
    gset = {g for g in (genres or []) if g}

    if age is not None:
        if gset & FAMILY_GENRES and age >= 16:
            hit = ", ".join(sorted(gset & FAMILY_GENRES))
            return True, f"{hit}-Genre, aber FSK {age}"
        if gset & MATURE_GENRES and age <= 6:
            hit = ", ".join(sorted(gset & MATURE_GENRES))
            return True, f"Genre {hit}, aber nur FSK {age}"

    # Alte, unklare Freigabe weicht stark vom Vorschlag ab
    if official and official not in VALID_RATINGS and suggested:
        a_old, a_new = _age_of(official), _age_of(suggested)
        if a_old is not None and a_new is not None and abs(a_old - a_new) >= 12:
            return True, f"Freigabe '{official}' weicht stark von Vorschlag {suggested} ab"
    return False, ""


def analyze(item: dict) -> dict:
    """read-only: fsk_suspicious/fsk_reason setzen."""
    suspicious, reason = plausibility(
        item.get("official_rating"), item.get("fsk_suggested"), item.get("genres")
    )
    # Fehlende Freigabe, obwohl ein Vorschlag existiert -> auch markieren
    if not item.get("official_rating") and item.get("fsk_suggested"):
        suspicious = True
        reason = reason or f"Keine Freigabe gesetzt (Vorschlag {item['fsk_suggested']})"
    item["fsk_suspicious"] = 1 if suspicious else 0
    item["fsk_reason"] = reason
    return item


_admin_uid = None


def _emby_admin_uid(base_url: str, headers: dict) -> str:
    """Admin-User-Id ermitteln und cachen (für Massen-Schreiben)."""
    global _admin_uid
    if _admin_uid:
        return _admin_uid
    users = requests.get(f"{base_url}/emby/Users", headers=headers, timeout=15).json()
    _admin_uid = next((u["Id"] for u in users if u.get("Policy", {}).get("IsAdministrator")), None)
    if not _admin_uid:
        raise RuntimeError("Kein Emby-Admin gefunden")
    return _admin_uid


def write_emby(source_id: str, rating: str) -> None:
    """AUSNAHME: Freigabe aktiv nach Emby schreiben. Nur mit ALLOW_EMBY_WRITE.

    Server-Adresse und Token kommen aus der in der DB gespeicherten Emby-Quelle
    (Phase 4a) - nicht mehr aus ENV-Variablen.
    """
    if not config.ALLOW_EMBY_WRITE:
        raise RuntimeError("Zurückschreiben ist deaktiviert (ALLOW_EMBY_WRITE=0).")
    from . import crypto, sources
    src = sources.get_by_kind("emby")
    if not src or not src["enabled"]:
        raise RuntimeError("Emby ist nicht konfiguriert.")
    base_url = (src["base_url"] or "").rstrip("/")
    headers = {"X-Emby-Token": crypto.decrypt(src["secret"] or "")}
    uid = _emby_admin_uid(base_url, headers)
    full = requests.get(
        f"{base_url}/emby/Users/{uid}/Items/{source_id}", headers=headers, timeout=15
    ).json()
    full["OfficialRating"] = rating or None
    resp = requests.post(
        f"{base_url}/emby/Items/{source_id}",
        headers={**headers, "Content-Type": "application/json"},
        data=json.dumps(full), timeout=30,
    )
    resp.raise_for_status()
