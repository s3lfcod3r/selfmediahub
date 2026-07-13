<div align="center">

<img src="assets/logo.png" width="260" alt="SelfMediaHub logo" />

**Read-only analysis, monitoring &amp; quality-control layer for your media library — Emby, Jellyfin, Plex and local folders. Never a media server, never writes back.**

[![Build](https://github.com/s3lfcod3r/selfmediahub/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/s3lfcod3r/selfmediahub/actions/workflows/docker-publish.yml)
![Version](https://img.shields.io/badge/version-0.2.4-33A78C)
![License](https://img.shields.io/badge/license-MIT-8A9CAA)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688)
![Database](https://img.shields.io/badge/db-SQLite-1DB8D4)
![Docker](https://img.shields.io/badge/docker-GHCR-2496ED)

**Works with:** Emby · Jellyfin · Plex · local folders · TMDb

[English](#-english) · [Deutsch](#-deutsch)

</div>

---

<a id="-english"></a>

## 🇬🇧 English

**SelfMediaHub** is a standalone **analysis, monitoring and quality-control layer** on top of the
media library you already have. It is deliberately **not** a media server and **not** a manager:
it reads your libraries **read-only** through their APIs, stores everything in its **own database**,
and never touches your originals.

The goal: see at a glance **what you have, what's missing, what can be improved, and what's new.**

Part of the **Self** family (SelfMailer, SelfDashboard, SelfArchiver …) — same design system, same
deploy style (GHCR → Unraid).

> **TL;DR** — read-only layer over Emby/Jellyfin/Plex/local · cover + list views with rich filters ·
> per-title detail with episodes, tracks &amp; file paths · exact resolutions · FSK ratings you can set
> from the cover · own tag system + rule engine · background scans &amp; webhook alerts · one container,
> own SQLite DB.

### 📑 Table of contents
[Features](#-features) · [Views &amp; interaction](#️-views--interaction) · [Age ratings (FSK)](#-age-ratings-fsk) · [Tags &amp; rules](#️-tags--rules) · [Monitoring](#-monitoring--notifications) · [Quick start](#-quick-start-docker) · [Unraid](#-unraid) · [Configuration](#️-configuration) · [Architecture](#-architecture) · [Development](#️-development) · [Roadmap](#️-roadmap)

### ✨ Features

**📥 Sources — all read-only**
- **Emby**, **Jellyfin**, **Plex** via their APIs + **local folders** (filename parsing)
- Several sources at once; a broken source never stops the others
- **Own SQLite database** under `/data` — fully independent from your media servers

**🔎 Analysis &amp; enrichment**
- Technical data: **exact resolution, HDR / Dolby Vision, video codec, audio &amp; subtitle tracks, file size, runtime**
- **TMDb** enrichment: German age rating, genres, season/episode counts, series status
- **Completeness**: present vs. released episodes, missing-episode detection
- **Real resolutions** — an 800p downscale shows `800p`, not rounded to `720p`; only true UHD is `4K`

### 🖥️ Views &amp; interaction

- **Cover view** (poster grid) with rating, resolution and completeness badges + tag chips
- **List view** with toggleable, sortable columns
- **Filters**: search · library · type (movie/series) · rating (incl. *no rating* &amp; *FSK suspicious*) · **resolution** (incl. *under 720p* and every real height) · tags · series status
- **Stat tiles**: total · films · series · 4K/UHD · incomplete · without rating
- **Detail window** (click a poster/title): resolution `W × H`, HDR, codec, size, runtime, **audio &amp; subtitle languages**, genres, TMDb data and the **file path**
- For series: the **full episode list per season** — every episode **expandable** with its own resolution, codec, size, languages, subtitles and path; **missing episodes are highlighted**

### 🌐 Interface &amp; account

- **Bilingual interface (German / English)** — pick the UI language under **Settings → General**; every screen, filter and message is fully translated
- **Optional single-account login** — protect the instance with username + password; toggle it on/off under **Settings → Account**

### 🎫 Age ratings (FSK)

- **Set the rating right on the cover** — click the FSK corner → a small popup → pick a value → **saved to Emby instantly**
- Or from the **detail window** (dropdown + save)
- **TMDb suggestions** (recommended German rating)
- **Plausibility check** flags implausible ratings (e.g. family genre but FSK 18); **“Passt so”** acknowledges deliberate ones so they stop being reported
- Writing to Emby is the **one exception** to the read-only rule — enabled via `ALLOW_EMBY_WRITE=1` (off by default). It powers parental control: set the rating here, and Emby's per-account max-rating does the blocking.

### 🏷️ Tags &amp; rules

- **Own tag system** — name, colour, icon, priority; assigned manually or automatically
- **Rule engine** with **AND / OR / NOT**, multiple conditions &amp; actions, priorities and on/off
- Rule fields include resolution/height/width, codecs, languages, completeness, rating, genres and more

### 🔔 Monitoring &amp; notifications

- **Background scan** every N hours (`SCAN_INTERVAL_HOURS`)
- **Webhook notification** (Discord / ntfy / Apprise) when new content appears

### 🚀 Quick start (Docker)

```bash
docker run -d --name selfmediahub -p 8092:8092 \
  -v /path/to/data:/data \
  -e TMDB_API_KEY=YOUR_TMDB_KEY \
  ghcr.io/s3lfcod3r/selfmediahub:latest
```

Open `http://<host>:8092/`, add your media source under **Settings → Data sources**
(URL + API key, stored encrypted), then click **”Neu einlesen”** (re-scan) in the top right.

### 🧩 Unraid

Template at [`unraid/selfmediahub.xml`](unraid/selfmediahub.xml). Add via **Add Container → Template**,
map `/data` to `/mnt/user/appdata/selfmediahub`, and fill in the sources you use.

### ⚙️ Configuration

> **Media sources** (Emby/Jellyfin/Plex/local folders) are configured in the UI under
> **Settings → Data sources** and stored **encrypted** in the database — not via environment variables.

| Variable | Meaning |
|----------|---------|
| `TMDB_API_KEY` | themoviedb.org v3 — ratings, genres, completeness |
| `SCAN_INTERVAL_HOURS` | background scan every N hours (`0` = off) |
| `NOTIFY_WEBHOOK_URL` | JSON webhook for notifications |
| `ALLOW_EMBY_WRITE` | `1` = write FSK ratings back to Emby (default `0`, read-only) |
| `PORT` / `DATA_DIR` | web port (`8092`) / DB location (`/data`) |

### 🧱 Architecture

```
app/
├── connectors/   emby · jellyfin · plex · local        (read-only)
├── services/     sync · tmdb · analysis · completeness · fsk · rules · tags · scheduler · notify
├── routes/       pages (HTML) · api (JSON) · health
├── templates/    index · tags · rules · setup · _topbar · _modal
├── static/       css/tokens · css/app · js/common · js/app · js/detail
└── db.py         SQLite (own data under /data)
```

**Stack:** Python 3.12 · FastAPI · Uvicorn · Jinja2 (server-rendered) · vanilla JS · SQLite · Docker.
No Node build step — the UI is server-rendered.

### 🛠️ Development

```bash
pip install -r requirements.txt
cp .env.example .env         # fill in values, DATA_DIR=./data
python -m app.main
```

### 🗺️ Roadmap

All core phases are **live**: read-only import, own DB, cover + list views, technical/quality analysis,
TMDb enrichment, completeness, tag system + rule engine, monitoring &amp; notifications, and the FSK
quality control ported from `emby-fsk-manager`.

**Live:** DB-backed source management in the UI (Emby/Jellyfin/Plex/local) with a list +
add/edit dialog, encrypted credentials, per-source library selection, a directory browser for
local paths, and **multiple sources of the same type** (e.g. two Emby servers).

**Planned:** ffprobe for local files (per-file technical), movie-series / sequel tracking.

---

<a id="-deutsch"></a>

## 🇩🇪 Deutsch

**SelfMediaHub** legt sich als eigenständige **Analyse-, Monitoring- und Qualitätskontroll-Schicht**
über deine bestehende Mediathek. Es ist ausdrücklich **kein** Medienserver und **kein** Manager:
Es liest deine Bibliotheken **nur lesend** über deren APIs, speichert alles in einer **eigenen
Datenbank** und fasst deine Originaldaten niemals an.

Ziel: auf einen Blick sehen, **was vorhanden ist, was fehlt, was verbessert werden kann und was neu
dazugekommen ist.**

Teil der **Self**-Familie (SelfMailer, SelfDashboard, SelfArchiver …) — gleiches Design-System,
gleiche Deploy-Art (GHCR → Unraid).

> **Kurz gesagt** — read-only Schicht über Emby/Jellyfin/Plex/lokal · Cover- + Listenansicht mit
> vielen Filtern · Detail je Titel mit Episoden, Spuren &amp; Pfaden · echte Auflösungen · FSK direkt
> am Cover setzbar · eigenes Tag-System + Regel-Engine · Hintergrund-Scans &amp; Webhook-Meldungen ·
> ein Container, eigene SQLite-DB.

### 📑 Inhalt
[Funktionen](#-funktionen) · [Ansichten &amp; Bedienung](#️-ansichten--bedienung) · [Freigaben (FSK)](#-freigaben-fsk) · [Tags &amp; Regeln](#️-tags--regeln) · [Monitoring](#-monitoring--benachrichtigungen) · [Schnellstart](#-schnellstart-docker) · [Unraid](#-unraid-1) · [Konfiguration](#️-konfiguration) · [Architektur](#-architektur) · [Entwicklung](#️-entwicklung) · [Roadmap](#️-roadmap-1)

### ✨ Funktionen

**📥 Quellen — alle read-only**
- **Emby**, **Jellyfin**, **Plex** über deren APIs + **lokale Ordner** (Dateinamen-Analyse)
- Mehrere Quellen gleichzeitig; eine defekte Quelle stoppt die anderen nie
- **Eigene SQLite-Datenbank** unter `/data` — komplett unabhängig vom Medienserver

**🔎 Analyse &amp; Anreicherung**
- Technik: **exakte Auflösung, HDR / Dolby Vision, Video-Codec, Audio- &amp; Untertitelspuren, Dateigröße, Laufzeit**
- **TMDb**-Abgleich: deutsche Freigabe, Genres, Staffel-/Episodenzahl, Serienstatus
- **Vollständigkeit**: vorhandene vs. veröffentlichte Episoden, Erkennung fehlender Folgen
- **Echte Auflösungen** — ein 800p-Downscale zeigt `800p` statt gerundet `720p`; nur echtes UHD ist `4K`

### 🖥️ Ansichten &amp; Bedienung

- **Coveransicht** (Poster-Grid) mit Freigabe-, Auflösungs- und Vollständigkeits-Badges + Tag-Chips
- **Listenansicht** mit zuschaltbaren, sortierbaren Spalten
- **Filter**: Suche · Bibliothek · Typ (Film/Serie) · Freigabe (inkl. *ohne Freigabe* &amp; *FSK auffällig*) · **Auflösung** (inkl. *unter 720p* und jede echte Höhe) · Tags · Serien-Status
- **Statistik-Kacheln**: Gesamt · Filme · Serien · 4K/UHD · unvollständig · ohne Freigabe
- **Detail-Fenster** (Klick auf Poster/Titel): Auflösung `B × H`, HDR, Codec, Größe, Laufzeit, **Audio- &amp; Untertitelsprachen**, Genres, TMDb-Daten und der **Pfad im Verzeichnis**
- Bei Serien: die **komplette Episodenliste je Staffel** — jede Folge **aufklappbar** mit eigener Auflösung, Codec, Größe, Sprachen, Untertiteln und Pfad; **fehlende Folgen sind markiert**

### 🌐 Oberfläche &amp; Konto

- **Zweisprachige Oberfläche (Deutsch / Englisch)** — UI-Sprache unter **Einstellungen → Allgemein** wählen; alle Ansichten, Filter und Meldungen sind vollständig übersetzt
- **Optionaler Ein-Konto-Login** — Instanz mit Benutzername + Passwort schützen; unter **Einstellungen → Konto** an/aus

### 🎫 Freigaben (FSK)

- **FSK direkt am Cover setzen** — Klick auf die FSK-Ecke → kleines Popup → Wert wählen → **sofort nach Emby gespeichert**
- Oder im **Detail-Fenster** (Dropdown + Speichern)
- **TMDb-Vorschläge** (empfohlene deutsche Freigabe)
- **Plausibilitätscheck** markiert unplausible Freigaben (z. B. Familien-Genre, aber FSK 18); **„Passt so“** bestätigt bewusste Freigaben, damit sie nicht mehr gemeldet werden
- Das Schreiben nach Emby ist die **einzige Ausnahme** zur read-only-Regel — aktivierbar über `ALLOW_EMBY_WRITE=1` (Standard aus). Damit steuerst du die Kindersicherung: hier die Freigabe setzen, die Sperre übernimmt Embys maximale Freigabe je Konto.

### 🏷️ Tags &amp; Regeln

- **Eigenes Tag-System** — Name, Farbe, Icon, Priorität; manuell oder automatisch vergeben
- **Regel-Engine** mit **UND / ODER / NICHT**, mehreren Bedingungen &amp; Aktionen, Prioritäten und aktiv/inaktiv
- Regel-Felder u. a. Auflösung/Höhe/Breite, Codecs, Sprachen, Vollständigkeit, Freigabe, Genres

### 🔔 Monitoring &amp; Benachrichtigungen

- **Hintergrund-Scan** alle N Stunden (`SCAN_INTERVAL_HOURS`)
- **Webhook-Benachrichtigung** (Discord / ntfy / Apprise) bei neuen Inhalten

### 🚀 Schnellstart (Docker)

```bash
docker run -d --name selfmediahub -p 8092:8092 \
  -v /pfad/zu/daten:/data \
  -e TMDB_API_KEY=DEIN_TMDB_KEY \
  ghcr.io/s3lfcod3r/selfmediahub:latest
```

Dann `http://<host>:8092/` öffnen, unter **Einstellungen → Datenquellen** deine Quelle
anlegen (URL + API-Key, verschlüsselt gespeichert) und oben rechts **„Neu einlesen”** klicken.

### 🧩 Unraid

Template unter [`unraid/selfmediahub.xml`](unraid/selfmediahub.xml). Über **Add Container → Template**
einbinden, `/data` auf `/mnt/user/appdata/selfmediahub` mappen und die gewünschten Quellen ausfüllen.

### ⚙️ Konfiguration

> **Datenquellen** (Emby/Jellyfin/Plex/lokale Ordner) werden im UI unter
> **Einstellungen → Datenquellen** angelegt und **verschlüsselt** in der Datenbank
> gespeichert — nicht mehr über Umgebungsvariablen.

| Variable | Bedeutung |
|----------|-----------|
| `TMDB_API_KEY` | themoviedb.org v3 — Freigaben, Genres, Vollständigkeit |
| `SCAN_INTERVAL_HOURS` | Hintergrund-Scan alle N Stunden (`0` = aus) |
| `NOTIFY_WEBHOOK_URL` | JSON-Webhook für Benachrichtigungen |
| `ALLOW_EMBY_WRITE` | `1` = FSK-Freigaben nach Emby schreiben (Standard `0`, read-only) |
| `PORT` / `DATA_DIR` | Web-Port (`8092`) / DB-Ablage (`/data`) |

### 🧱 Architektur

```
app/
├── connectors/   emby · jellyfin · plex · local        (nur lesend)
├── services/     sync · tmdb · analysis · completeness · fsk · rules · tags · scheduler · notify
├── routes/       pages (HTML) · api (JSON) · health
├── templates/    index · tags · rules · setup · _topbar · _modal
├── static/       css/tokens · css/app · js/common · js/app · js/detail
└── db.py         SQLite (eigene Daten unter /data)
```

**Stack:** Python 3.12 · FastAPI · Uvicorn · Jinja2 (server-gerendert) · Vanilla-JS · SQLite · Docker.
Kein Node-Build — die Oberfläche wird server-seitig gerendert.

### 🛠️ Entwicklung

```bash
pip install -r requirements.txt
cp .env.example .env         # Werte eintragen, DATA_DIR=./data
python -m app.main
```

### 🗺️ Roadmap

Alle Kern-Phasen sind **live**: read-only Import, eigene DB, Cover- + Listenansicht, Technik-/Qualitäts-
analyse, TMDb-Abgleich, Vollständigkeit, Tag-System + Regel-Engine, Monitoring &amp; Benachrichtigungen
sowie die FSK-Qualitätskontrolle (portiert aus `emby-fsk-manager`).

**Live:** DB-gestützte Quellenverwaltung im UI (Emby/Jellyfin/Plex/lokal) mit Liste +
Anlegen/Bearbeiten-Dialog, verschlüsselte Zugangsdaten, Bibliotheks-Auswahl je Quelle,
Verzeichnis-Browser für lokale Pfade und **mehrere Quellen desselben Typs** (z. B. zwei Emby-Server).

**Geplant:** ffprobe für lokale Dateien (Technik pro Datei), Filmreihen-/Sequel-Tracking.

---

<div align="center">
<sub>Part of the <strong>Self</strong> family · built read-only, your data stays yours.</sub>
</div>
