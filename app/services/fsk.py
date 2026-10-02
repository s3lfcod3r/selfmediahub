"""FSK-Qualitätskontrolle (aus emby-fsk-manager portiert).

- analyze(): read-only. Prüft Freigabe auf Plausibilität, nutzt TMDb-Vorschlag.
- write_emby(): AUSNAHME - schreibt eine Freigabe aktiv nach Emby zurück.
  Nur wenn ALLOW_EMBY_WRITE=1. SelfMediaHub ist sonst strikt read-only.
"""
import json

import requests

from .. import config, db
from . import ratings

VALID_RATINGS = ["DE-0", "DE-6", "DE-12", "DE-16", "DE-18",
                 "FSK-0", "FSK-6", "FSK-12", "FSK-16", "FSK-18"]
FAMILY_GENRES = {"Animation", "Familie", "Family", "Kids", "Kinder", "Komoedie", "Komödie", "Comedy"}
MATURE_GENRES = {"Horror", "Krieg", "War", "Thriller", "Krimi", "Crime"}


def plausibility(official: str, suggested: str, genres: list):
    """Gibt (suspicious, reason). Nutzt vorhandene oder vorgeschlagene Freigabe."""
    rating = official or suggested
    age = ratings.age_of(rating)
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
        a_old, a_new = ratings.age_of(official), ratings.age_of(suggested)
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


def refresh_locks() -> dict:
    """Sperr-Status (rating_locked) fuer alle Emby/Jellyfin-Items neu aus der Quelle
    lesen und die lokale DB aktualisieren. Read-only gegen die Quelle - kein
    ALLOW_EMBY_WRITE noetig.

    Grund fuer diesen Extra-Schritt: der Sync liest die Item-Liste, und Emby
    liefert die Sperr-Info (LockedFields/LockData) im Listen-Endpoint nicht mit.
    Erst der Einzel-Item-Abruf (fetch_rating_locks) kennt den echten Stand.
    """
    from . import sources
    checked = changed = locked = 0
    for conn in sources.build_connectors():
        if getattr(conn, "kind", None) not in ("emby", "jellyfin"):
            continue
        rows = db.query(
            "SELECT id, source_id, rating_locked FROM media_items WHERE source_ref=?",
            (conn.source_ref,),
        )
        state = conn.fetch_rating_locks([r["source_id"] for r in rows])
        for r in rows:
            new = state.get(r["source_id"])
            if new is None:  # Item nicht lesbar -> vorhandenen Wert behalten
                continue
            checked += 1
            locked += new
            if int(r["rating_locked"] or 0) != new:
                db.execute("UPDATE media_items SET rating_locked=? WHERE id=?", (new, r["id"]))
                changed += 1
    return {"checked": checked, "locked": locked, "changed": changed}


# Admin-User-Id je Server cachen (base_url -> uid) - bei mehreren Emby-Instanzen
# darf die UID nicht serveruebergreifend wiederverwendet werden.
_admin_uid_by_url: dict = {}


def _emby_admin_uid(base_url: str, headers: dict) -> str:
    """Admin-User-Id des Servers ermitteln und je base_url cachen."""
    if base_url in _admin_uid_by_url:
        return _admin_uid_by_url[base_url]
    users = requests.get(f"{base_url}/emby/Users", headers=headers, timeout=15).json()
    uid = next((u["Id"] for u in users if u.get("Policy", {}).get("IsAdministrator")), None)
    if not uid:
        raise RuntimeError("Kein Emby-Admin gefunden")
    _admin_uid_by_url[base_url] = uid
    return uid


def write_emby(source_ref: int, source_id: str, rating: str) -> None:
    """AUSNAHME: Freigabe aktiv nach Emby schreiben. Nur mit ALLOW_EMBY_WRITE.

    Ziel-Server ist die konkrete Emby-Instanz des Items (``source_ref``) -
    wichtig, sobald mehrere Emby-Quellen existieren. Adresse und Token kommen
    aus der in der DB gespeicherten Quelle, nicht aus ENV-Variablen.
    """
    if not config.ALLOW_EMBY_WRITE:
        raise RuntimeError("Zurückschreiben ist deaktiviert (ALLOW_EMBY_WRITE=0).")
    from . import crypto, sources
    src = sources.get_source(source_ref) if source_ref is not None else None
    if not src or src["kind"] != "emby" or not src["enabled"]:
        raise RuntimeError("Emby ist nicht konfiguriert.")
    base_url = (src["base_url"] or "").rstrip("/")
    headers = {"X-Emby-Token": crypto.decrypt(src["secret"] or "")}
    uid = _emby_admin_uid(base_url, headers)
    full = requests.get(
        f"{base_url}/emby/Users/{uid}/Items/{source_id}", headers=headers, timeout=15
    ).json()
    full["OfficialRating"] = rating or None
    # Feld sperren, damit ein Emby-Metadaten-Refresh die Korrektur nicht ueberschreibt
    # (auch "Kein Rating" = leer + gesperrt). Vorhandene Sperren bleiben erhalten.
    locked = full.get("LockedFields") or []
    if "OfficialRating" not in locked:
        locked.append("OfficialRating")
    full["LockedFields"] = locked
    resp = requests.post(
        f"{base_url}/emby/Items/{source_id}",
        headers={**headers, "Content-Type": "application/json"},
        data=json.dumps(full), timeout=30,
    )
    resp.raise_for_status()
