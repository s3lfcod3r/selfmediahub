"""Vollständigkeit: vorhandene vs. veroeffentlichte Episoden (aus TMDb)."""


def compute(item: dict) -> dict:
    """Setzt completeness ('complete'|'incomplete'|'unknown') + missing_episodes."""
    if item.get("item_type") != "Serie":
        return item

    have = item.get("have_episodes")
    total = item.get("tmdb_episodes")
    if total and have is not None:
        missing = max(0, total - have)
        item["missing_episodes"] = missing
        item["completeness"] = "complete" if missing == 0 else "incomplete"
    else:
        item["completeness"] = "unknown"
    return item
