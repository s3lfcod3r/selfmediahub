"""Technische Analyse: Auflösung und HDR-Format aus Rohwerten ableiten."""


def resolution_label(width, height):
    """Echte Auflösung nach Bildhöhe. Nur echtes UHD wird zu '4K'
    zusammengefasst; alles andere zeigt die tatsaechliche Höhe (z.B. 800p,
    1600p), damit eigene Render-Auflösungen korrekt erscheinen."""
    w, h = width or 0, height or 0
    if w >= 3800 or h >= 2000:
        return "4K"
    if h > 0:
        return f"{h}p"
    return None


def normalize_hdr(raw):
    if not raw:
        return None
    r = str(raw).lower()
    if "dv" in r or "dolby" in r:
        return "Dolby Vision"
    if "hdr10+" in r or "hdr10plus" in r:
        return "HDR10+"
    if "hdr" in r:
        return "HDR10"
    if r == "sdr":
        return "SDR"
    return raw


def enrich(item: dict) -> dict:
    """Abgeleitete Technik-Felder in-place ergaenzen."""
    item["resolution"] = resolution_label(item.get("width"), item.get("height"))
    item["hdr"] = normalize_hdr(item.get("hdr"))
    return item
