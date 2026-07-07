"""Konfiguration aus Umgebungsvariablen. Keine Secrets im Code."""
import os

APP_NAME = "SelfMediaHub"
VERSION = "0.2.0"

# Eigene Daten - komplett getrennt von jedem Medienserver.
DATA_DIR = os.environ.get("DATA_DIR", "/data")
DB_PATH = os.environ.get("DB_PATH", os.path.join(DATA_DIR, "selfmediahub.db"))

PORT = int(os.environ.get("PORT", "8092"))

# --- Quelle: Emby (nur lesend) -----------------------------------------
EMBY_URL = os.environ.get("EMBY_URL", "").rstrip("/")
EMBY_API_KEY = os.environ.get("EMBY_API_KEY", "").strip()

# --- Quelle: Jellyfin (Emby-kompatible API, nur lesend) ----------------
JELLYFIN_URL = os.environ.get("JELLYFIN_URL", "").rstrip("/")
JELLYFIN_API_KEY = os.environ.get("JELLYFIN_API_KEY", "").strip()

# --- Quelle: Plex (nur lesend) -----------------------------------------
PLEX_URL = os.environ.get("PLEX_URL", "").rstrip("/")
PLEX_TOKEN = os.environ.get("PLEX_TOKEN", "").strip()

# --- Quelle: lokale Ordner (Komma-getrennt) ----------------------------
LOCAL_PATHS = [p.strip() for p in os.environ.get("LOCAL_PATHS", "").split(",") if p.strip()]

# --- Externe Metadaten -------------------------------------------------
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "").strip()

# --- Automatik & Benachrichtigung --------------------------------------
# Hintergrund-Scan alle N Stunden (0 = aus).
SCAN_INTERVAL_HOURS = float(os.environ.get("SCAN_INTERVAL_HOURS", "0") or "0")
# Generischer JSON-Webhook (z.B. Apprise, Discord, ntfy-Bridge). Leer = aus.
NOTIFY_WEBHOOK_URL = os.environ.get("NOTIFY_WEBHOOK_URL", "").strip()

# --- Ausnahme: aktives Zurueckschreiben nach Emby (FSK) ----------------
# Standard AUS - SelfMediaHub ist read-only. Nur bewusst aktivieren.
ALLOW_EMBY_WRITE = os.environ.get("ALLOW_EMBY_WRITE", "0").strip() in ("1", "true", "yes")


def emby_configured() -> bool:
    return bool(EMBY_URL and EMBY_API_KEY)


def jellyfin_configured() -> bool:
    return bool(JELLYFIN_URL and JELLYFIN_API_KEY)


def plex_configured() -> bool:
    return bool(PLEX_URL and PLEX_TOKEN)


def local_configured() -> bool:
    return bool(LOCAL_PATHS)


def any_source_configured() -> bool:
    return (
        emby_configured()
        or jellyfin_configured()
        or plex_configured()
        or local_configured()
    )


def tmdb_enabled() -> bool:
    return bool(TMDB_API_KEY)
