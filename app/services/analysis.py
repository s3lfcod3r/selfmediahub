"""Technische Analyse: Aufloesung und HDR-Format aus Rohwerten ableiten."""


def resolution_label(width, height):
    w, h = width or 0, height or 0
    if h >= 2000 or w >= 3800:
        return "4K"
    if h >= 1000:
        return "1080p"
    if h >= 700:
        return "720p"
    if h >= 570:
        return "576p"
    if h >= 400:
        return "480p"
    if h > 0:
        return "SD"
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
