<div align="center">

# SelfMediaHub

**Read-only Analyse- und Übersichtsschicht für deine Mediathek.**
Kein weiterer Medienserver – eine intelligente Sicht auf das, was du schon hast.

![Status](https://img.shields.io/badge/status-Phase%201%20(MVP)-33a78c?style=flat-square)
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
Es liest deine Bibliothek **nur lesend** über die Server-API ein, speichert alles in einer
**eigenen Datenbank** und fasst deine Originaldaten niemals an.

Ziel: auf einen Blick sehen, **was vorhanden ist, was fehlt, was verbessert werden kann und
was neu dazugekommen ist.**

### Funktionen (Phase 1 – MVP)

- **Read-only Import aus Emby** – Filme & Serien über die Emby-API, ohne Rückschreiben
- **Eigene Datenbank** (SQLite unter `/data`) – komplett unabhängig vom Medienserver
- **Coveransicht** – Kachel-Grid wie im Medienserver, mit Freigabe-Badge & Typ
- **Listenansicht** – frei konfigurierbare Tabelle (Spalten zuschaltbar, sortierbar)
- **Filter** nach Bibliothek, Typ (Film/Serie) und Freigabe (inkl. „ohne Freigabe")
- **Live-Suche** und **Statistik-Übersicht** (Gesamt, Filme, Serien, ohne Freigabe)
- **Self-Design** – dark-first, Hell/Dunkel-Umschalter

### Roadmap

| Phase | Inhalt |
|-------|--------|
| 1 ✅ | Fundament: Import, eigene DB, Cover- + Listenansicht |
| 2 | Technik-/Qualitätsanalyse (Codec, Auflösung, HDR, Sprach-/Untertitelspuren) + TMDb |
| 3 | Vollständigkeit: fehlende Episoden/Staffeln, neue Releases |
| 4 | Eigenes Tag-System + Regel-Engine (UND/ODER/NICHT) |
| 5 | Monitoring & Benachrichtigungen, Hintergrundscans |
| 6 | Weitere Quellen (Plex, Jellyfin, lokale Ordner) |

> Der frühere **FSK-Check** (aus `emby-fsk-manager`) wandert in Phase 2/3 als Modul „Qualitätskontrolle" hierher.

### Schnellstart (Docker)

```bash
docker run -d --name selfmediahub -p 8092:8092 \
  -v /pfad/zu/daten:/data \
  -e EMBY_URL=http://192.168.1.19:8096 \
  -e EMBY_API_KEY=DEIN_EMBY_KEY \
  ghcr.io/s3lfcod3r/selfmediahub:latest
```

Dann `http://<host>:8092/` im Browser öffnen und oben rechts **„Neu einlesen"** klicken.

### Konfiguration

| Variable | Pflicht | Bedeutung |
|----------|---------|-----------|
| `EMBY_URL` | ja | Adresse des Emby-Servers, z. B. `http://192.168.1.19:8096` |
| `EMBY_API_KEY` | ja | Emby → Einstellungen → Erweitert → API-Schlüssel |
| `TMDB_API_KEY` | nein | themoviedb.org v3-Key (erst ab Phase 2) |
| `PORT` | nein | Port der Weboberfläche (Standard `8092`) |
| `DATA_DIR` | nein | Ablageort der DB (Standard `/data`) |

### Unraid

Template unter [`unraid/selfmediahub.xml`](unraid/selfmediahub.xml). Über **Add Container → Template**
einbinden und die Variablen ausfüllen. `/data` auf `/mnt/user/appdata/selfmediahub` mappen.

### Lokal entwickeln

```bash
pip install -r requirements.txt
cp .env.example .env         # Werte eintragen, DATA_DIR=./data
# Variablen laden, dann:
python -m app.main
```

---

## English

**SelfMediaHub** is a standalone **read-only analysis, monitoring and quality-control layer**
on top of your existing media library. It is deliberately **not** a media server and **not**
a manager: it reads your library **read-only** via the server API, stores everything in its
**own database**, and never touches your original data.

Goal: see at a glance **what you have, what is missing, what can be improved, and what is new.**

### Features (Phase 1 – MVP)

- **Read-only import from Emby** – movies & series via the Emby API, no write-back
- **Own database** (SQLite under `/data`) – fully independent from the media server
- **Cover view** – poster grid like a media server, with rating badge & type
- **List view** – configurable table (toggleable, sortable columns)
- **Filters** by library, type (movie/series) and rating (incl. "no rating")
- **Live search** and a **stats overview**
- **Self design** – dark-first with a light/dark toggle

### Roadmap

| Phase | Scope |
|-------|-------|
| 1 ✅ | Foundation: import, own DB, cover + list view |
| 2 | Technical/quality analysis (codec, resolution, HDR, audio/subtitle tracks) + TMDb |
| 3 | Completeness: missing episodes/seasons, new releases |
| 4 | Own tag system + rule engine (AND/OR/NOT) |
| 5 | Monitoring & notifications, background scans |
| 6 | More sources (Plex, Jellyfin, local folders) |

### Quick start (Docker)

```bash
docker run -d --name selfmediahub -p 8092:8092 \
  -v /path/to/data:/data \
  -e EMBY_URL=http://192.168.1.19:8096 \
  -e EMBY_API_KEY=YOUR_EMBY_KEY \
  ghcr.io/s3lfcod3r/selfmediahub:latest
```

Open `http://<host>:8092/` and click **"Neu einlesen"** (re-scan) in the top right.

### License

MIT

---

<div align="center">
<sub>Part of the <strong>Self</strong> suite · built read-only, your data stays yours.</sub>
</div>
