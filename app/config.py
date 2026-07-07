"""Konfiguration aus Umgebungsvariablen. Keine Secrets im Code."""
import os

APP_NAME = "SelfMediaHub"
VERSION = "0.1.0"

# Eigene Daten - komplett getrennt von jedem Medienserver.
DATA_DIR = os.environ.get("DATA_DIR", "/data")
DB_PATH = os.environ.get("DB_PATH", os.path.join(DATA_DIR, "selfmediahub.db"))

PORT = int(os.environ.get("PORT", "8092"))

# Emby-Quelle (nur lesend ueber die API).
EMBY_URL = os.environ.get("EMBY_URL", "").rstrip("/")
EMBY_API_KEY = os.environ.get("EMBY_API_KEY", "").strip()

# Optional - erst ab Phase 2 (Metadaten-Abgleich) genutzt.
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "").strip()


def emby_configured() -> bool:
    """True, wenn eine Emby-Verbindung vollstaendig konfiguriert ist."""
    return bool(EMBY_URL and EMBY_API_KEY)


def any_source_configured() -> bool:
    """True, sobald mindestens eine Medienquelle konfiguriert ist."""
    return emby_configured()
