"""Abdeckung der primaeren Sprache je Titel berechnen (Ton & Untertitel).

Nutzt die in der DB gespeicherten Episoden - kein erneuter Emby-Abruf noetig.
Ergebnis: pro media_item ``primary_audio_pct`` / ``primary_sub_pct`` (0-100):
- Serie: Anteil der Folgen, die die primaere Sprache haben
- Film: 100 wenn vorhanden, sonst 0 (nie "teilweise")

Wird nach jedem Sync aufgerufen und wenn die primaere Sprache umgestellt wird.
"""
import json

from .. import db
from . import settings as settings_service

# Verschiedene Sprachcodes auf einen kanonischen 2-Buchstaben-Code abbilden,
# damit ger/deu/de zusammenfallen (analog zur Frontend-Logik shortLang).
_CANON = {
    "ger": "de", "deu": "de", "de": "de", "eng": "en", "en": "en",
    "fre": "fr", "fra": "fr", "fr": "fr", "spa": "es", "es": "es",
    "ita": "it", "it": "it", "jpn": "ja", "ja": "ja", "rus": "ru", "ru": "ru",
    "tur": "tr", "tr": "tr", "pol": "pl", "pl": "pl", "nld": "nl", "dut": "nl", "nl": "nl",
    "por": "pt", "pt": "pt", "kor": "ko", "ko": "ko", "chi": "zh", "zho": "zh", "zh": "zh",
    "ara": "ar", "ar": "ar",
}


def _canon(code) -> str:
    c = str(code or "").lower()
    return _CANON.get(c, c[:2])


def _has(langs, canon: str) -> bool:
    return any(_canon(lang) == canon for lang in (langs or []))


def _pct(count: int, total: int):
    return round(100 * count / total) if total else None


def recompute() -> int:
    """Abdeckung fuer alle Titel neu berechnen. Gibt die Anzahl aktualisierter Titel zurueck."""
    primary = _canon(settings_service.get("display.primary_language", "ger"))
    updates = []
    for row in db.query("SELECT id, item_type, audio_langs, subtitle_langs FROM media_items"):
        if row["item_type"] == "Serie":
            eps = db.query("SELECT audio_langs, subtitle_langs FROM episodes WHERE item_id=?", (row["id"],))
            total = len(eps)
            if total:
                a = sum(1 for e in eps if _has(json.loads(e["audio_langs"] or "[]"), primary))
                s = sum(1 for e in eps if _has(json.loads(e["subtitle_langs"] or "[]"), primary))
                apct, spct = _pct(a, total), _pct(s, total)
            else:
                apct = spct = None
        else:
            apct = 100 if _has(json.loads(row["audio_langs"] or "[]"), primary) else 0
            spct = 100 if _has(json.loads(row["subtitle_langs"] or "[]"), primary) else 0
        updates.append((apct, spct, row["id"]))

    with db.get_conn() as conn:
        conn.executemany(
            "UPDATE media_items SET primary_audio_pct=?, primary_sub_pct=? WHERE id=?", updates)
        conn.commit()
    return len(updates)
