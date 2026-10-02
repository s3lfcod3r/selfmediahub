"""Konfiguration aus Umgebungsvariablen. Keine Secrets im Code."""
import logging
import os

logger = logging.getLogger("selfmediahub.config")

APP_NAME = "SelfMediaHub"
VERSION = "0.7.1"

# GitHub-Repo fuer die Update-Pruefung (vergleicht mit dem neuesten Release).
GITHUB_REPO = os.environ.get("GITHUB_REPO", "s3lfcod3r/selfmediahub").strip()

# Notausgang: Authentifizierung komplett ueberbruecken (z.B. Passwort vergessen).
# Am Container setzen (SMH_DISABLE_AUTH=1), dann greift keine Login-Wand.
DISABLE_AUTH = os.environ.get("SMH_DISABLE_AUTH", "0").strip() in ("1", "true", "yes")

# Sitzungs-Cookie immer mit Secure ausliefern (nur HTTPS). Normalerweise wird das
# je Anfrage erkannt (Schema bzw. X-Forwarded-Proto); dieser Schalter erzwingt es.
COOKIE_SECURE = os.environ.get("SMH_COOKIE_SECURE", "0").strip() in ("1", "true", "yes")

# Adressen von Reverse Proxys, deren X-Forwarded-For geglaubt werden darf
# (kommagetrennt, z.B. SMH_TRUSTED_PROXIES=192.168.1.10). Ohne Eintrag zaehlt
# fuer die Anmelde-Bremse ausschliesslich die tatsaechliche Gegenstelle - sonst
# koennte sich jeder mit einem selbst gesetzten Header darum herummogeln.
TRUSTED_PROXIES = {p.strip() for p in os.environ.get("SMH_TRUSTED_PROXIES", "").split(",") if p.strip()}

# Eigene Daten - komplett getrennt von jedem Medienserver.
DATA_DIR = os.environ.get("DATA_DIR", "/data")
DB_PATH = os.environ.get("DB_PATH", os.path.join(DATA_DIR, "selfmediahub.db"))

# Defensives Parsen: ungueltige ENV-Werte (z.B. PORT=abc) duerfen den Import
# nicht crashen; statt dessen Default mit Warning.
def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning("%s=%r kein gueltiger Zahlwert -> Default %d", name, raw, default)
        return default

def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        logger.warning("%s=%r kein gueltiger Zahlwert -> Default %r", name, raw, default)
        return default

PORT = _int_env("PORT", 8092)

# Log-Stufe (DEBUG/INFO/WARNING/ERROR/CRITICAL). Steuert eigene Logs UND uvicorn.
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").strip().upper()

# --- Datenquellen (Emby/Jellyfin/Plex/lokal) ---------------------------
# Ab Phase 4a werden Quellen im UI angelegt und in der DB gespeichert
# (verschluesselt), nicht mehr ueber ENV-Variablen. Siehe services/sources.py.

# --- Externe Metadaten -------------------------------------------------
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "").strip()
# Eingebauter TheTVDB-Projekt-Key. Wird beim CI-Build in app/config_buildkey.py
# geschrieben (nie im Repo, gitignored) und hier importiert; fehlt die Datei
# (lokaler Bau), bleibt der Key leer. Eine ENV-Variable TVDB_API_KEY kann ihn
# zusaetzlich ueberschreiben (z.B. fuer Tests).
try:
    from .config_buildkey import BUILTIN_TVDB_KEY as _BUILTIN_TVDB_KEY
except ImportError:
    _BUILTIN_TVDB_KEY = ""
TVDB_API_KEY = (os.environ.get("TVDB_API_KEY", "").strip()
                or (_BUILTIN_TVDB_KEY or "").strip())

# --- Automatik & Benachrichtigung --------------------------------------
# Hintergrund-Scan alle N Stunden (0 = aus).
SCAN_INTERVAL_HOURS = _float_env("SCAN_INTERVAL_HOURS", 0.0)
# Generischer JSON-Webhook (z.B. Apprise, Discord, ntfy-Bridge). Leer = aus.
NOTIFY_WEBHOOK_URL = os.environ.get("NOTIFY_WEBHOOK_URL", "").strip()

# --- Ausnahme: aktives Zurückschreiben nach Emby (FSK) ----------------
# Standard AUS - SelfMediaHub ist read-only. Nur bewusst aktivieren.
ALLOW_EMBY_WRITE = os.environ.get("ALLOW_EMBY_WRITE", "0").strip() in ("1", "true", "yes")
