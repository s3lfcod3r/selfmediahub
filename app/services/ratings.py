"""Alters-/Freigabe-Normalisierung + Uebersetzung zwischen Rating-Systemen.

Pivot ist das normalisierte Mindestalter (Zahl): jedes System -> Alter -> Ziel.
Beim Rendern ins Zielsystem wird bei fehlendem Raster HOCH gerundet
(Jugendschutz - lieber zu streng als zu lasch). Phase 5c.2, erweitert Phase 5d
(Fix 6) um internationale Buchstaben-Systeme (MPAA, US-TV, BBFC).
"""
import re

# Zielsysteme -> aufsteigende Leiter aus (Mindestalter, Anzeige-Label).
# Die Alters-Stufen entsprechen bewusst den Werten aus ``age_of`` fuer die
# jeweils nativen Labels, damit ein native Rohwert beim Rendern exakt auf sein
# eigenes Label faellt (kein faelschliches "uebersetzt"-Symbol). 'age' = Sonderfall
# "Zahl+Plus" (verlustfrei, jedes Alter). Phase 5d Fix 6.
SYSTEMS = {
    "fsk":  [(0, "FSK 0"), (6, "FSK 6"), (12, "FSK 12"), (16, "FSK 16"), (18, "FSK 18")],
    "usk":  [(0, "USK 0"), (6, "USK 6"), (12, "USK 12"), (16, "USK 16"), (18, "USK 18")],
    "pegi": [(3, "PEGI 3"), (7, "PEGI 7"), (12, "PEGI 12"), (16, "PEGI 16"), (18, "PEGI 18")],
    # US-Kino (MPAA). PG-13 -> 12, R -> 16 (deckt sich mit age_of-Synonymen).
    "mpaa": [(0, "G"), (6, "PG"), (12, "PG-13"), (16, "R"), (18, "NC-17")],
    # US-Fernsehen. TV-Y7/TV-G werden erkannt, aber aufs naechste Renderband
    # (TV-PG) abgebildet; TV-MA ist die hoechste Stufe (deckt 17+ ab).
    "ustv": [(0, "TV-Y"), (6, "TV-PG"), (12, "TV-14"), (16, "TV-MA")],
    # UK (BBFC). U/PG/12/15/18 - "15" hat wirklich Alter 15 (kein FSK-Raster).
    "bbfc": [(0, "U"), (6, "PG"), (12, "12"), (15, "15"), (18, "18")],
    "age":  None,
}
DEFAULT_ART = "fsk"

# Rohwerte, die als nativ (nicht "uebersetzt") gelten. Fuer FSK/USK/PEGI ueber
# ein Prefix (z.B. "de-16", "fsk 16"); fuer die Buchstaben-Systeme ueber die
# Label-Menge (siehe _SYS_LABELS). 'age' kann jedes Alter verlustfrei zeigen.
_NATIVE_PREFIX = {"fsk": ("fsk", "de"), "usk": ("usk",), "pegi": ("pegi",)}
_SYS_LABELS = {art: {lbl.lower() for _, lbl in buckets}
               for art, buckets in SYSTEMS.items() if buckets}

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
    ``rounded`` = True, wenn das gewaehlte Band nicht exakt dem Alter entspricht."""
    if age is None:
        return None, False
    buckets = SYSTEMS.get(art)
    if not buckets:  # 'age' -> Zahl+Plus, verlustfrei
        return f"{age}+", False
    for bage, label in buckets:
        if bage >= age:
            return label, bage != age
    # Kein Band >= Alter -> hoechste Stufe (System kennt kein hoeheres Band).
    top_age, top_label = buckets[-1]
    return top_label, top_age != age


def _is_native(rating, art) -> bool:
    if art == "age":
        return True  # "Zahl+Plus" kann jedes Alter verlustfrei zeigen
    s = str(rating).strip().lower()
    if s in _SYS_LABELS.get(art, ()):   # exaktes System-Label (z.B. "R", "TV-14")
        return True
    return any(s.startswith(p) for p in _NATIVE_PREFIX.get(art, ()))


def translate(rating, art):
    """(text, translated). ``translated`` = True, wenn der Wert nicht nativ im
    Zielsystem vorlag (aus anderem System abgeleitet) oder hochgerundet wurde."""
    age = age_of(rating)
    if age is None:
        return None, False
    text, rounded = render(age, art)
    if _is_native(rating, art) and not rounded:
        return text, False
    return text, True
