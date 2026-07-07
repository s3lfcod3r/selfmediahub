<div align="center">

# SelfMediaHub

**Read-only Analyse-, Monitoring- und Qualitätskontroll-Schicht für deine Mediathek.**
Kein weiterer Medienserver – eine intelligente Sicht auf das, was du schon hast.

![Status](https://img.shields.io/badge/status-aktiv-33a78c?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.12-1db8d4?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-GHCR-2496ed?style=flat-square&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-8a9caa?style=flat-square)

[Deutsch](#deutsch) · [English](#english)

</div>

---

## Deutsch

**SelfMediaHub** legt sich als eigenständige **Analyse-, Monitoring- und Qualitätskontroll-Schicht**
über deine bestehende Mediathek. Es ist ausdrücklich **kein** Medienserver und **kein** Manager:
Es liest deine Bibliotheken **nur lesend** über die jeweilige API, speichert alles in einer
**eigenen Datenbank** und fasst deine Originaldaten niemals an.

Ziel: auf einen Blick sehen, **was vorhanden ist, was fehlt, was verbessert werden kann und
was neu dazugekommen ist.**

### Funktionen

**Quellen (alle read-only)**
- **Emby**, **Jellyfin**, **Plex** über deren API + **lokale Ordner** (Dateinamen-Analyse)
- Mehrere Quellen gleichzeitig; eine defekte Quelle stoppt die anderen nicht

**Analyse & Übersicht**
- **Coveransicht** (Poster-Grid) mit Freigabe-, Auflösungs- und Vollständigkeits-Badges
- **Frei konfigurierbare Listenansicht** (Spalten zuschaltbar, sortierbar)
- Technik: **Auflösung, HDR/Dolby Vision, Video-Codec, Audio-/Untertitelspuren, Laufzeit**
- **TMDb-Abgleich**: deutsche FSK, Genres, Staffel-/Episodenzahl, Serienstatus

**Qualitätskontrolle** (eigene Seite)
- Inhalte **ohne Freigabe**, **unplausible FSK** (Genre-vs-Alter-Check, aus emby-fsk-manager portiert)
- **Unvollständige Serien** (vorhandene vs. veröffentlichte Episoden via TMDb)
- **Filme unter 720p**
- **FSK-Vorschlag** aus TMDb; optionales Zurückschreiben nach Emby (Schalter `ALLOW_EMBY_WRITE`, Standard aus)

**Tags & Automatik**
- **Eigenes Tag-System** (Name, Farbe, Icon, Priorität), manuell + automatisch
- **Regel-Engine** mit **UND/ODER/NICHT**, mehreren Bedingungen & Aktionen, Prioritäten, aktiv/inaktiv

**Automatik & Monitoring**
- **Hintergrund-Scan** alle N Stunden (`SCAN_INTERVAL_HOURS`)
- **Benachrichtigung** bei neuen Inhalten über generischen JSON-Webhook (Discord/ntfy/Apprise)

### Roadmap

| Phase | Inhalt | Stand |
|-------|--------|-------|
| 1 | Fundament: Import, eigene DB, Cover- + Listenansicht | ✅ |
| 2 | Technik-/Qualitätsanalyse + TMDb | ✅ |
| 3 | Vollständigkeit: fehlende Episoden/Staffeln | ✅ |
| 4 | Tag-System + Regel-Engine | ✅ |
| 5 | Monitoring & Benachrichtigungen, Hintergrundscans | ✅ |
| 6 | Weitere Quellen (Jellyfin, Plex, lokale Ordner) | ✅ |
| + | FSK-Qualitätskontrolle (aus emby-fsk-manager) | ✅ |

> Weiter geplant: pro-Episode-Technik für Serien, ffprobe für lokale Dateien, Filmreihen-/Sequel-Tracking, DB-gestützte Quellenverwaltung im UI.

### Schnellstart (Docker)

```bash
docker run -d --name selfmediahub -p 8092:8092 \
  -v /pfad/zu/daten:/data \
  -e EMBY_URL=http://192.168.1.19:8096 \
  -e EMBY_API_KEY=DEIN_EMBY_KEY \
  -e TMDB_API_KEY=DEIN_TMDB_KEY \
  ghcr.io/s3lfcod3r/selfmediahub:latest
```

Dann `http://<host>:8092/` öffnen und oben rechts **„Neu einlesen"** klicken.

### Konfiguration (Variablen)

| Variable | Bedeutung |
|----------|-----------|
| `EMBY_URL` / `EMBY_API_KEY` | Emby-Server (read-only) |
| `JELLYFIN_URL` / `JELLYFIN_API_KEY` | Jellyfin-Server (optional) |
| `PLEX_URL` / `PLEX_TOKEN` | Plex-Server (optional) |
| `LOCAL_PATHS` | lokale Ordner, Komma-getrennt (im Container) |
| `TMDB_API_KEY` | themoviedb.org v3 – FSK, Genres, Vollständigkeit |
| `SCAN_INTERVAL_HOURS` | Hintergrund-Scan alle N Stunden (0 = aus) |
| `NOTIFY_WEBHOOK_URL` | JSON-Webhook für Benachrichtigungen |
| `ALLOW_EMBY_WRITE` | `1` = FSK aktiv nach Emby schreiben (Standard `0`, read-only) |
| `PORT` / `DATA_DIR` | Web-Port (8092) / DB-Ablage (`/data`) |

### Unraid

Template unter [`unraid/selfmediahub.xml`](unraid/selfmediahub.xml). Über **Add Container → Template**
einbinden, `/data` auf `/mnt/user/appdata/selfmediahub` mappen, gewünschte Quellen ausfüllen.

### Architektur

```
app/
├── connectors/   emby · jellyfin · plex · local   (nur lesend)
├── services/     sync · tmdb · analysis · completeness · fsk · rules · tags · scheduler · notify
├── routes/       pages (HTML) · api (JSON) · health
├── templates/    index · quality · tags · rules · setup
└── db.py         SQLite (eigene Daten unter /data)
```

### Lokal entwickeln

```bash
pip install -r requirements.txt
cp .env.example .env         # Werte eintragen, DATA_DIR=./data
python -m app.main
```

---

## English

**SelfMediaHub** is a standalone **analysis, monitoring and quality-control layer** on top of your
existing media library. It is deliberately **not** a media server and **not** a manager: it reads your
libraries **read-only**, stores everything in its **own database**, and never touches your originals.

**Sources (read-only):** Emby, Jellyfin, Plex, and local folders — several at once.
**Analysis:** cover + configurable list view, resolution/HDR/codec/audio/subtitle tracks, TMDb enrichment (DE rating, genres, season/episode counts, status).
**Quality control:** missing ratings, implausible age ratings (ported from emby-fsk-manager), incomplete series, low-resolution films; TMDb rating suggestions with optional write-back to Emby (`ALLOW_EMBY_WRITE`, off by default).
**Tags & automation:** own tag system + rule engine (AND/OR/NOT, priorities).
**Monitoring:** background scans (`SCAN_INTERVAL_HOURS`) and webhook notifications for new content.

### Quick start (Docker)

```bash
docker run -d --name selfmediahub -p 8092:8092 \
  -v /path/to/data:/data \
  -e EMBY_URL=http://192.168.1.19:8096 \
  -e EMBY_API_KEY=YOUR_EMBY_KEY \
  -e TMDB_API_KEY=YOUR_TMDB_KEY \
  ghcr.io/s3lfcod3r/selfmediahub:latest
```

Open `http://<host>:8092/` and click **"Neu einlesen"** (re-scan) in the top right.

### License

MIT

---

<div align="center">
<sub>Part of the <strong>Self</strong> suite · built read-only, your data stays yours.</sub>
</div>
