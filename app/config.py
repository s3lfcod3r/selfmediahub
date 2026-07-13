"""Konfiguration aus Umgebungsvariablen. Keine Secrets im Code."""
import os

APP_NAME = "SelfMediaHub"
VERSION = "0.2.2"

# GitHub-Repo fuer die Update-Pruefung (vergleicht mit dem neuesten Release).
GITHUB_REPO = os.environ.get("GITHUB_REPO", "s3lfcod3r/selfmediahub").strip()

# Notausgang: Authentifizierung komplett ueberbruecken (z.B. Passwort vergessen).
# Am Container setzen (SMH_DISABLE_AUTH=1), dann greift keine Login-Wand.
DISABLE_AUTH = os.environ.get("SMH_DISABLE_AUTH", "0").strip() in ("1", "true", "yes")

# Eigene Daten - komplett getrennt von jedem Medienserver.
DATA_DIR = os.environ.get("DATA_DIR", "/data")
DB_PATH = os.environ.get("DB_PATH", os.path.join(DATA_DIR, "selfmediahub.db"))

PORT = int(os.environ.get("PORT", "8092"))

# --- Datenquellen (Emby/Jellyfin/Plex/lokal) ---------------------------
# Ab Phase 4a werden Quellen im UI angelegt und in der DB gespeichert
# (verschluesselt), nicht mehr ueber ENV-Variablen. Siehe services/sources.py.

# --- Externe Metadaten -------------------------------------------------
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "").strip()

# --- Automatik & Benachrichtigung --------------------------------------
# Hintergrund-Scan alle N Stunden (0 = aus).
SCAN_INTERVAL_HOURS = float(os.environ.get("SCAN_INTERVAL_HOURS", "0") or "0")
# Generischer JSON-Webhook (z.B. Apprise, Discord, ntfy-Bridge). Leer = aus.
NOTIFY_WEBHOOK_URL = os.environ.get("NOTIFY_WEBHOOK_URL", "").strip()

# --- Ausnahme: aktives Zurückschreiben nach Emby (FSK) ----------------
# Standard AUS - SelfMediaHub ist read-only. Nur bewusst aktivieren.
ALLOW_EMBY_WRITE = os.environ.get("ALLOW_EMBY_WRITE", "0").strip() in ("1", "true", "yes")


def tmdb_enabled() -> bool:
    return bool(TMDB_API_KEY)
