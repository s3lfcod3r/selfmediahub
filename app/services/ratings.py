"""Alters-/Freigabe-Normalisierung + Uebersetzung zwischen Rating-Systemen.

Pivot ist das normalisierte Mindestalter (Zahl): jedes System -> Alter -> Ziel.
Beim Rendern ins Zielsystem wird bei fehlendem Raster HOCH gerundet
(Jugendschutz - lieber zu streng als zu lasch). Phase 5c.2.
"""
import re

# Zielsysteme -> aufsteigende Alters-Stufen. 'age' = "Zahl+Plus" (verlustfrei).
SYSTEMS = {
    "fsk": [0, 6, 12, 16, 18],
    "usk": [0, 6, 12, 16, 18],
    "pegi": [3, 7, 12, 16, 18],
    "age": None,
}
DEFAULT_ART = "fsk"
_ART_LABEL = {"fsk": "FSK {}", "usk": "USK {}", "pegi": "PEGI {}"}
# Systeme, deren native Rohwerte NICHT als "uebersetzt" markiert werden.
_NATIVE_PREFIX = {"fsk": ("fsk", "de"), "usk": ("usk",), "pegi": ("pegi",)}

# Benannte Ratings + Synonyme -> Alter. Reine Zahlen/+Formen kommen per Regex.
_NAMED = {
    # deutsch / FSK-Sonderfaelle
    "ohne altersbeschränkung": 0, "ohne altersbeschraenkung": 0,
    "lehrprogramm": 0, "infoprogramm": 0,
    "keine jugendfreigabe": 18, "spio/jk": 18, "spio-jk": 18, "spiojk": 18,
    # US MPAA / TV
    "g": 0, "tv-g": 0, "tv-y": 0, "u": 0, "atp": 0, "l": 0, "k": 0, "c": 0,
    "pg": 6, "tv-y7": 6, "tv-pg": 6,
    "pg-13": 12, "tv-14": 12, "m12": 12, "ua13+": 12,
    "m16": 16, "ma15+": 16, "r": 16, "tv-ma": 16,
    "nc-17": 18, "m18": 18, "es-18": 18, "x": 18,
}
_DIGITS = re.compile(r"\d{1,2}")


def age_of(rating):
    """Rohes Rating (String) -> Mindestalter (0..18) oder None."""
    if rating is None:
        return None
    s = str(rating).strip().lower()
    if not s:
        return None
    if s in _NAMED:
        return _NAMED[s]
    m = _DIGITS.search(s)  # 'de-16', '16+', 'ab 16', '18' ...
    if m:
        return min(18, max(0, int(m.group())))
    return None


def resolve(ages) -> int | None:
    """Aus mehreren Laender-Altersangaben ein sicheres Alter waehlen: bei
    Uneinigkeit das HOECHSTE (Jugendschutz). None, wenn nichts Verwertbares."""
    vals = [a for a in ages if a is not None]
    return max(vals) if vals else None


def render(age, art):
    """(text, rounded). Alter im Zielsystem; bei fehlendem Raster HOCH gerundet.
    ``rounded`` = True, wenn das exakte Alter kein natives Raster des Systems ist."""
    if age is None:
        return None, False
    buckets = SYSTEMS.get(art)
    if not buckets:  # 'age' -> Zahl+Plus, verlustfrei
        return f"{age}+", False
    chosen = next((b for b in buckets if b >= age), buckets[-1])
    return _ART_LABEL.get(art, "{}").format(chosen), chosen != age


def _is_native(rating, art) -> bool:
    if art == "age":
        return True  # "Zahl+Plus" kann jedes Alter verlustfrei zeigen
    s = str(rating).strip().lower()
    return any(s.startswith(p) for p in _NATIVE_PREFIX.get(art, ()))


def translate(rating, art):
    """(text, translated). ``translated`` = True, wenn der Wert nicht nativ im
    Zielsystem vorlag (aus anderem System abgeleitet oder hochgerundet)."""
    age = age_of(rating)
    if age is None:
        return None, False
    text, rounded = render(age, art)
    native = (not rounded) and _is_native(rating, art)
    return text, not native
