<div align="center">

<img src="assets/logo.png" width="240" alt="SelfMediaHub logo" />

**Read-only analysis, monitoring &amp; quality-control layer for your media library — never a media server, never writes back.**<br>
*Nur lesende Analyse-, Monitoring- &amp; Qualitätskontroll-Schicht für deine Mediathek — nie ein Medienserver, schreibt nie zurück.*

[![Build](https://github.com/s3lfcod3r/selfmediahub/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/s3lfcod3r/selfmediahub/actions/workflows/docker-publish.yml)
![Version](https://img.shields.io/badge/version-0.7.1-33A78C)
![License](https://img.shields.io/badge/license-MIT-8A9CAA)
![Backend](https://img.shields.io/badge/backend-FastAPI-1F7763)
![Web](https://img.shields.io/badge/web-Jinja2%20%2B%20vanilla%20JS-43D3AD)
![Database](https://img.shields.io/badge/db-SQLite-1DB8D4)
![Deploy](https://img.shields.io/badge/deploy-GHCR%20%2B%20Unraid-6F95AD)

**[🇬🇧 English](#-english) · [🇩🇪 Deutsch](#-deutsch)**

📰 **What's new / Neuigkeiten** → [CHANGELOG.md](CHANGELOG.md)

</div>

---

<a id="-english"></a>

## 🇬🇧 English

**SelfMediaHub** is a standalone **analysis, monitoring and quality-control layer** on top of the media library you already have — **Emby, Jellyfin and Plex**, enriched with **TMDb** and **TheTVDB**. It is deliberately **not** a media server and **not** a manager: it reads your libraries **read-only** through their APIs, stores everything in its **own database**, and never touches your originals. The goal: see at a glance **what you have, what's missing, what can be improved, and what's new.**

Part of the **Self** family (SelfMailer, SelfDashboard, SelfArchiver …) — same design system, same deploy style (GHCR → Unraid).

> **TL;DR** — read-only layer over Emby/Jellyfin/Plex · cover + list views with rich filters · per-title detail with episodes, tracks &amp; file paths · exact resolutions · FSK ratings you can set from the cover · own tag system + rule engine · background scans &amp; webhook alerts · one container, own SQLite DB.

### 📑 Table of contents

[Features](#en-features) · [Views &amp; interaction](#en-views) · [Interface &amp; account](#en-interface) · [Age ratings (FSK)](#en-fsk) · [Tags &amp; rules](#en-tags-rules) · [Monitoring](#en-monitoring) · [Architecture](#en-architecture) · [Quick start](#en-quick-start) · [Unraid](#en-unraid) · [Configuration](#en-configuration) · [API](#en-api) · [Security](#en-security) · [Tech stack](#en-tech-stack) · [Development](#en-development) · [Roadmap](#en-roadmap)

<a id="en-features"></a>

### ✨ Features

**📥 Sources — all read-only**
- **Emby**, **Jellyfin** and **Plex** via their APIs
- Several sources at once — even **several of the same type** (e.g. two Emby servers); a broken source never stops the others
- **Own SQLite database** under `/data` — fully independent from your media servers

**🔎 Analysis &amp; enrichment**
- Technical data: **exact resolution, HDR / Dolby Vision, video codec, audio &amp; subtitle tracks, file size, runtime**
- **TMDb** and **TheTVDB** enrichment: German age rating, genres, season/episode counts, series status
- **Completeness per season**: present vs. released episodes, missing-episode detection, **season badges** on the cover
- **Episode order** Aired / DVD / Absolute per series
- **Real resolutions** — an 800p downscale shows `800p`, not rounded to `720p`; only true UHD is `4K`

<a id="en-views"></a>

### 🖥️ Views &amp; interaction

- **Cover view** (poster grid) with rating, resolution and season badges + tag chips
- **List view** with toggleable, sortable columns
- **Filters**: search · library · type (movie/series) · rating (incl. *no rating* &amp; *FSK suspicious*) · **resolution** (incl. *under 720p* and every real height) · codec · audio language · subtitles · tags · series status
- **Stat tiles**: total · films · series · 4K/UHD · incomplete · without rating
- **Detail window** (click a poster/title): resolution `W × H`, HDR, codec, size, runtime, **audio &amp; subtitle languages**, genres, metadata and the **file path**
- For series: the **full episode list per season** — every episode **expandable** with its own resolution, codec, size, languages, subtitles and path; **missing episodes are highlighted**

<a id="en-interface"></a>

### 🌐 Interface &amp; account

- **Bilingual interface (German / English)** — pick the UI language under **Settings → General**; every screen, filter and message is fully translated
- **Optional single-account login** — protect the instance with username + password; toggle it on/off under **Settings → Account**
- **Update check** — shows when a newer GitHub release is available (**Settings → About &amp; updates**)

<a id="en-fsk"></a>

### 🎫 Age ratings (FSK)

- **Set the rating right on the cover** — click the FSK corner → a small popup → pick a value → **saved to Emby instantly**
- Or from the **detail window** (dropdown + save), or on the **Ratings** page (list, editor, filters)
- **Suggestions** from TMDb/TheTVDB (recommended German rating, international ratings translated)
- **Plausibility check** flags implausible ratings (e.g. family genre but FSK 18); **“It's fine”** acknowledges deliberate ones so they stop being reported
- **Lock status &amp; drift detection** — shows which ratings are locked in Emby and reports when a rating was changed outside SelfMediaHub
- Writing to Emby is the **one exception** to the read-only rule — enabled via `ALLOW_EMBY_WRITE=1` (off by default). It powers parental control: set the rating here, and Emby's per-account max-rating does the blocking.

<a id="en-tags-rules"></a>

### 🏷️ Tags &amp; rules

- **Own tag system** — name, colour, icon, priority; assigned manually or automatically
- **Rule engine** with **AND / OR / NOT**, multiple conditions &amp; actions, priorities and on/off
- Rule fields include resolution/height/width, codecs, languages, completeness, rating, genres and more

<a id="en-monitoring"></a>

### 🔔 Monitoring &amp; notifications

- **Background scan** every N hours (`SCAN_INTERVAL_HOURS`)
- **Webhook notification** (Discord / ntfy / Apprise) when new content appears

<a id="en-architecture"></a>

### 🧭 Architecture

```text
app/
├── connectors/   emby · jellyfin · plex                                  (read-only)
├── services/     sync · tmdb · tvdb · analysis · completeness · seasons · episode_order
│                 fsk · ratings · rules · tags · scheduler · notify · sources · crypto · auth
├── routes/       pages (HTML) · api (JSON) · auth · health
├── i18n/         de · en
├── templates/    index · fsk · tags · rules · settings · login · setup · _topbar · _modal
├── static/       css/tokens · css/app · js/common · js/app · js/detail · js/fsk · js/settings
├── entrypoint.py drops root → PUID:PGID, then starts the app
└── db.py         SQLite (own data under /data)
```

<a id="en-quick-start"></a>

### 🚀 Quick start (Docker)

```bash
docker run -d --name selfmediahub -p 8092:8092 \
  -v /path/to/data:/data \
  -e TMDB_API_KEY=YOUR_TMDB_KEY \
  ghcr.io/s3lfcod3r/selfmediahub:latest

# or with the included docker-compose.yml (set TMDB_API_KEY there):
docker compose up -d
```

Open `http://<host>:8092/` → add your media source under **Settings → Data sources &amp; libraries** (URL + API key, stored encrypted) → click **Re-scan** in the top right.

<a id="en-unraid"></a>

### 📦 Unraid

Template at [`unraid/selfmediahub.xml`](unraid/selfmediahub.xml). Add via *Docker → Add Container → Template*, map `/data` to `/mnt/user/appdata/selfmediahub`, then add your sources in the UI.

> **⚠️ Permissions:** the container starts as root only to hand `/data` over to `PUID`:`PGID` (default `99` / `100` = `nobody:users`), then the app runs **non-root**. An existing data folder owned by root is taken over automatically.

<a id="en-configuration"></a>

### ⚙️ Configuration

> **Media sources** (Emby/Jellyfin/Plex) are configured in the UI under **Settings → Data sources &amp; libraries** and stored **encrypted** in the database — not via environment variables.

Environment variables (no common prefix; security switches start with `SMH_`).

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `TMDB_API_KEY` | – | – | themoviedb.org v3 — ratings, genres, completeness. Empty = these features off. |
| `TVDB_API_KEY` | – | built-in key | Overrides the TheTVDB project key embedded at CI build time (e.g. for tests) |
| `SCAN_INTERVAL_HOURS` | – | `0` | Background scan every N hours (`0` = off) |
| `NOTIFY_WEBHOOK_URL` | – | – | JSON webhook for notifications (Discord / ntfy / Apprise). Empty = off. |
| `ALLOW_EMBY_WRITE` | – | `0` | `1` = write FSK ratings back to Emby (read-only by default) |
| `PORT` | – | `8092` | Web port |
| `DATA_DIR` | – | `/data` | DB location (`./data` for local development) |
| `DB_PATH` | – | `$DATA_DIR/selfmediahub.db` | SQLite file |
| `LOG_LEVEL` | – | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` / `CRITICAL` |
| `PUID` / `PGID` | – | `99` / `100` | User/group the app runs as |
| `SMH_DISABLE_AUTH` | – | `0` | Emergency exit: `1` bypasses the login (e.g. forgotten password) |
| `SMH_COOKIE_SECURE` | – | `0` | `1` = always send the session cookie HTTPS-only |
| `SMH_TRUSTED_PROXIES` | – | – | Comma-separated reverse-proxy IPs whose `X-Forwarded-For` is trusted |
| `GITHUB_REPO` | – | `s3lfcod3r/selfmediahub` | Repository used for the update check |

<a id="en-api"></a>

### 🔌 API overview

Base path `/api`, authentication via the session cookie of the web login (when login is enabled). Interactive docs: `http://<host>:8092/docs`.

| Group | Endpoints (excerpt) |
|---|---|
| **Sync** | `sync`, `sync/status` |
| **Items** | `items/{id}/detail`, `items/{id}/order`, `items/{id}/tags`, `image/{id}` |
| **Sources** | `sources` (CRUD), `sources/{id}/test`, `sources/{id}/libraries`, `providers` |
| **Tags &amp; rules** | `tags` (CRUD), `rules` (CRUD), `rules/apply` |
| **FSK** | `fsk/write`, `fsk/write-bulk`, `fsk/ack`, `fsk/refresh-locks`, `fsk/accept-drift` |
| **Settings** | `settings`, `account/*`, `update`, `update/check` |
| **Health** | `health` (open; details only with a valid session) |

<a id="en-security"></a>

### 🛡️ Security

- **Read-only** towards all media servers; the only write path (FSK → Emby) is off unless `ALLOW_EMBY_WRITE=1`
- Source credentials **Fernet-encrypted at rest**; login password hashed with **PBKDF2-HMAC-SHA256** (240,000 rounds)
- Signed `httpOnly` / `SameSite=Lax` session cookie; `Secure` automatically behind HTTPS or forced via `SMH_COOKIE_SECURE`
- **Login throttling**: 5 failed attempts per IP → locked for 15 minutes; proxy headers only trusted from `SMH_TRUSTED_PROXIES`
- `/api/health` reveals nothing without a session; error messages are neutral (details go to the log)
- Page data embedded as escaped JSON (no XSS via media titles or file paths)
- App runs **non-root**; dependencies and GitHub Actions **pinned** to fixed versions
- **Deliberate trade-offs** (documented): the encryption key lives in the same database as the encrypted data (no manual key handling); `SMH_DISABLE_AUTH=1` switches the login off completely

Security update history → [CHANGELOG.md](CHANGELOG.md) (entries marked 🔒).

<a id="en-tech-stack"></a>

### 🧱 Tech stack

| Part | Tech |
|---|---|
| Backend | Python 3.12 · FastAPI · Uvicorn · requests · cryptography |
| Web | Jinja2 (server-rendered) · vanilla JS — no Node build step |
| Data | SQLite (own data under `/data`) · TMDb · TheTVDB |
| Deploy | Docker (drops to non-root) · GHCR · Unraid |

<a id="en-development"></a>

### 🛠️ Development

```bash
pip install -r requirements.txt
cp .env.example .env         # fill in values, DATA_DIR=./data
python -m app.main
```

**Tests:** there is no automated test suite yet.

<a id="en-roadmap"></a>

### 🗺️ Roadmap

- [x] Read-only import from Emby / Jellyfin / Plex into an own DB
- [x] Cover + list views, technical/quality analysis, TMDb + TheTVDB enrichment
- [x] Completeness per season, episode order Aired / DVD / Absolute
- [x] Tag system + rule engine, monitoring &amp; notifications
- [x] FSK quality control (ported from `emby-fsk-manager`), lock status, drift detection
- [x] Source management in the UI: list + add/edit dialog, encrypted credentials, per-source library selection, **multiple sources of the same type**
- [x] Bilingual UI, optional login, update check
- [ ] Movie-series / sequel tracking

<p align="right"><a href="#-english">⬆ back to top</a></p>

---

<a id="-deutsch"></a>

## 🇩🇪 Deutsch

**SelfMediaHub** legt sich als eigenständige **Analyse-, Monitoring- und Qualitätskontroll-Schicht** über deine bestehende Mediathek — **Emby, Jellyfin und Plex**, angereichert mit **TMDb** und **TheTVDB**. Es ist ausdrücklich **kein** Medienserver und **kein** Manager: Es liest deine Bibliotheken **nur lesend** über deren APIs, speichert alles in einer **eigenen Datenbank** und fasst deine Originaldaten niemals an. Ziel: auf einen Blick sehen, **was vorhanden ist, was fehlt, was verbessert werden kann und was neu dazugekommen ist.**

Teil der **Self**-Familie (SelfMailer, SelfDashboard, SelfArchiver …) — gleiches Design-System, gleicher Deploy-Stil (GHCR → Unraid).

> **Kurz** — nur lesende Schicht über Emby/Jellyfin/Plex · Cover- + Listenansicht mit vielen Filtern · Detail je Titel mit Episoden, Spuren &amp; Pfaden · echte Auflösungen · FSK direkt am Cover setzbar · eigenes Tag-System + Regel-Engine · Hintergrund-Scans &amp; Webhook-Meldungen · ein Container, eigene SQLite-DB.

### 📑 Inhaltsverzeichnis

[Funktionen](#de-funktionen) · [Ansichten &amp; Bedienung](#de-ansichten) · [Oberfläche &amp; Konto](#de-oberflaeche) · [Freigaben (FSK)](#de-fsk) · [Tags &amp; Regeln](#de-tags-regeln) · [Monitoring](#de-monitoring) · [Architektur](#de-architektur) · [Schnellstart](#de-schnellstart) · [Unraid](#de-unraid) · [Konfiguration](#de-konfiguration) · [API](#de-api) · [Sicherheit](#de-sicherheit) · [Tech-Stack](#de-tech-stack) · [Entwicklung](#de-entwicklung) · [Roadmap](#de-roadmap)

<a id="de-funktionen"></a>

### ✨ Funktionen

**📥 Quellen — alle nur lesend**
- **Emby**, **Jellyfin** und **Plex** über deren APIs
- Mehrere Quellen gleichzeitig — auch **mehrere desselben Typs** (z. B. zwei Emby-Server); eine defekte Quelle stoppt die anderen nie
- **Eigene SQLite-Datenbank** unter `/data` — komplett unabhängig vom Medienserver

**🔎 Analyse &amp; Anreicherung**
- Technik: **exakte Auflösung, HDR / Dolby Vision, Video-Codec, Audio- &amp; Untertitelspuren, Dateigröße, Laufzeit**
- Abgleich mit **TMDb** und **TheTVDB**: deutsche Freigabe, Genres, Staffel-/Episodenzahl, Serienstatus
- **Vollständigkeit je Staffel**: vorhandene vs. veröffentlichte Episoden, Erkennung fehlender Folgen, **Staffel-Badges** am Cover
- **Episoden-Reihenfolge** Ausstrahlung / DVD / Absolut je Serie
- **Echte Auflösungen** — ein 800p-Downscale zeigt `800p` statt gerundet `720p`; nur echtes UHD ist `4K`

<a id="de-ansichten"></a>

### 🖥️ Ansichten &amp; Bedienung

- **Coveransicht** (Poster-Raster) mit Freigabe-, Auflösungs- und Staffel-Badges + Tag-Chips
- **Listenansicht** mit zuschaltbaren, sortierbaren Spalten
- **Filter**: Suche · Bibliothek · Typ (Film/Serie) · Freigabe (inkl. *ohne Freigabe* &amp; *FSK auffällig*) · **Auflösung** (inkl. *unter 720p* und jede echte Höhe) · Codec · Audiosprache · Untertitel · Tags · Serien-Status
- **Statistik-Kacheln**: Gesamt · Filme · Serien · 4K/UHD · unvollständig · ohne Freigabe
- **Detail-Fenster** (Klick auf Poster/Titel): Auflösung `B × H`, HDR, Codec, Größe, Laufzeit, **Audio- &amp; Untertitelsprachen**, Genres, Metadaten und der **Pfad im Verzeichnis**
- Bei Serien: die **komplette Episodenliste je Staffel** — jede Folge **aufklappbar** mit eigener Auflösung, Codec, Größe, Sprachen, Untertiteln und Pfad; **fehlende Folgen sind markiert**

<a id="de-oberflaeche"></a>

### 🌐 Oberfläche &amp; Konto

- **Zweisprachige Oberfläche (Deutsch / Englisch)** — UI-Sprache unter **Einstellungen → Allgemein** wählen; alle Ansichten, Filter und Meldungen sind vollständig übersetzt
- **Optionaler Ein-Konto-Login** — Instanz mit Benutzername + Passwort schützen; unter **Einstellungen → Konto** an/aus
- **Update-Prüfung** — zeigt an, wenn ein neueres GitHub-Release vorliegt (**Einstellungen → Über &amp; Updates**)

<a id="de-fsk"></a>

### 🎫 Freigaben (FSK)

- **FSK direkt am Cover setzen** — Klick auf die FSK-Ecke → kleines Popup → Wert wählen → **sofort nach Emby gespeichert**
- Oder im **Detail-Fenster** (Dropdown + Speichern) oder auf der **FSK-Seite** (Liste, Editor, Filter)
- **Vorschläge** aus TMDb/TheTVDB (empfohlene deutsche Freigabe, internationale Freigaben übersetzt)
- **Plausibilitätscheck** markiert unplausible Freigaben (z. B. Familien-Genre, aber FSK 18); **„Passt so“** bestätigt bewusste Freigaben, damit sie nicht mehr gemeldet werden
- **Sperr-Status &amp; Drift-Erkennung** — zeigt, welche Freigaben in Emby gesperrt sind, und meldet, wenn eine Freigabe außerhalb von SelfMediaHub geändert wurde
- Das Schreiben nach Emby ist die **einzige Ausnahme** zur Nur-Lesen-Regel — aktivierbar über `ALLOW_EMBY_WRITE=1` (Standard aus). Damit steuerst du die Kindersicherung: hier die Freigabe setzen, die Sperre übernimmt Embys maximale Freigabe je Konto.

<a id="de-tags-regeln"></a>

### 🏷️ Tags &amp; Regeln

- **Eigenes Tag-System** — Name, Farbe, Icon, Priorität; manuell oder automatisch vergeben
- **Regel-Engine** mit **UND / ODER / NICHT**, mehreren Bedingungen &amp; Aktionen, Prioritäten und aktiv/inaktiv
- Regel-Felder u. a. Auflösung/Höhe/Breite, Codecs, Sprachen, Vollständigkeit, Freigabe, Genres und mehr

<a id="de-monitoring"></a>

### 🔔 Monitoring &amp; Benachrichtigungen

- **Hintergrund-Scan** alle N Stunden (`SCAN_INTERVAL_HOURS`)
- **Webhook-Benachrichtigung** (Discord / ntfy / Apprise) bei neuen Inhalten

<a id="de-architektur"></a>

### 🧭 Architektur

```text
app/
├── connectors/   emby · jellyfin · plex                                  (nur lesend)
├── services/     sync · tmdb · tvdb · analysis · completeness · seasons · episode_order
│                 fsk · ratings · rules · tags · scheduler · notify · sources · crypto · auth
├── routes/       pages (HTML) · api (JSON) · auth · health
├── i18n/         de · en
├── templates/    index · fsk · tags · rules · settings · login · setup · _topbar · _modal
├── static/       css/tokens · css/app · js/common · js/app · js/detail · js/fsk · js/settings
├── entrypoint.py gibt Root ab → PUID:PGID, startet dann die App
└── db.py         SQLite (eigene Daten unter /data)
```

<a id="de-schnellstart"></a>

### 🚀 Schnellstart (Docker)

```bash
docker run -d --name selfmediahub -p 8092:8092 \
  -v /pfad/zu/daten:/data \
  -e TMDB_API_KEY=DEIN_TMDB_KEY \
  ghcr.io/s3lfcod3r/selfmediahub:latest

# oder mit der mitgelieferten docker-compose.yml (TMDB_API_KEY dort eintragen):
docker compose up -d
```

`http://<host>:8092/` öffnen → unter **Einstellungen → Datenquellen &amp; Bibliotheken** deine Quelle anlegen (URL + API-Key, verschlüsselt gespeichert) → oben rechts **„Neu einlesen“** klicken.

<a id="de-unraid"></a>

### 📦 Unraid

Vorlage unter [`unraid/selfmediahub.xml`](unraid/selfmediahub.xml). Über *Docker → Add Container → Template* einbinden, `/data` auf `/mnt/user/appdata/selfmediahub` mappen und danach die Quellen in der Oberfläche anlegen.

> **⚠️ Rechte:** der Container startet nur als root, um `/data` an `PUID`:`PGID` zu übergeben (Standard `99` / `100` = `nobody:users`); danach läuft die App **ohne Root**. Ein bestehender Datenordner, der root gehört, wird automatisch übernommen.

<a id="de-konfiguration"></a>

### ⚙️ Konfiguration

> **Datenquellen** (Emby/Jellyfin/Plex) werden in der Oberfläche unter **Einstellungen → Datenquellen &amp; Bibliotheken** angelegt und **verschlüsselt** in der Datenbank gespeichert — nicht über Umgebungsvariablen.

Umgebungsvariablen (kein gemeinsames Präfix; Sicherheits-Schalter beginnen mit `SMH_`).

| Variable | Pflicht | Standard | Zweck |
|---|---|---|---|
| `TMDB_API_KEY` | – | – | themoviedb.org v3 — Freigaben, Genres, Vollständigkeit. Leer = diese Funktionen aus. |
| `TVDB_API_KEY` | – | eingebauter Key | Überschreibt den beim CI-Build eingebetteten TheTVDB-Projekt-Key (z. B. für Tests) |
| `SCAN_INTERVAL_HOURS` | – | `0` | Hintergrund-Scan alle N Stunden (`0` = aus) |
| `NOTIFY_WEBHOOK_URL` | – | – | JSON-Webhook für Benachrichtigungen (Discord / ntfy / Apprise). Leer = aus. |
| `ALLOW_EMBY_WRITE` | – | `0` | `1` = FSK-Freigaben nach Emby schreiben (Standard: nur lesend) |
| `PORT` | – | `8092` | Web-Port |
| `DATA_DIR` | – | `/data` | DB-Ablage (`./data` bei lokaler Entwicklung) |
| `DB_PATH` | – | `$DATA_DIR/selfmediahub.db` | SQLite-Datei |
| `LOG_LEVEL` | – | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` / `CRITICAL` |
| `PUID` / `PGID` | – | `99` / `100` | Nutzer/Gruppe, unter dem die App läuft |
| `SMH_DISABLE_AUTH` | – | `0` | Notausgang: `1` schaltet den Login ab (z. B. Passwort vergessen) |
| `SMH_COOKIE_SECURE` | – | `0` | `1` = Sitzungs-Cookie immer nur über HTTPS senden |
| `SMH_TRUSTED_PROXIES` | – | – | Kommagetrennte Reverse-Proxy-IPs, deren `X-Forwarded-For` geglaubt wird |
| `GITHUB_REPO` | – | `s3lfcod3r/selfmediahub` | Repository für die Update-Prüfung |

<a id="de-api"></a>

### 🔌 API-Übersicht

Basispfad `/api`, Anmeldung über das Sitzungs-Cookie des Web-Logins (wenn der Login aktiv ist). Interaktive Doku: `http://<host>:8092/docs`.

| Bereich | Endpunkte (Auszug) |
|---|---|
| **Sync** | `sync`, `sync/status` |
| **Titel** | `items/{id}/detail`, `items/{id}/order`, `items/{id}/tags`, `image/{id}` |
| **Quellen** | `sources` (CRUD), `sources/{id}/test`, `sources/{id}/libraries`, `providers` |
| **Tags &amp; Regeln** | `tags` (CRUD), `rules` (CRUD), `rules/apply` |
| **FSK** | `fsk/write`, `fsk/write-bulk`, `fsk/ack`, `fsk/refresh-locks`, `fsk/accept-drift` |
| **Einstellungen** | `settings`, `account/*`, `update`, `update/check` |
| **Health** | `health` (offen; Details nur mit gültiger Sitzung) |

<a id="de-sicherheit"></a>

### 🛡️ Sicherheit

- **Nur lesend** gegenüber allen Medienservern; der einzige Schreibweg (FSK → Emby) ist aus, solange `ALLOW_EMBY_WRITE=1` nicht gesetzt ist
- Zugangsdaten der Quellen **Fernet-verschlüsselt** gespeichert; Login-Passwort mit **PBKDF2-HMAC-SHA256** gehasht (240.000 Runden)
- Signiertes Sitzungs-Cookie mit `httpOnly` / `SameSite=Lax`; `Secure` automatisch hinter HTTPS oder erzwungen über `SMH_COOKIE_SECURE`
- **Anmelde-Bremse**: 5 Fehlversuche je IP → 15 Minuten gesperrt; Proxy-Header werden nur von `SMH_TRUSTED_PROXIES` geglaubt
- `/api/health` verrät ohne Sitzung nichts; Fehlermeldungen sind neutral (Einzelheiten stehen im Log)
- Seitendaten als maskiertes JSON eingebettet (kein XSS über Medientitel oder Dateipfade)
- App läuft **ohne Root**; Pakete und GitHub-Actions auf **feste Versionen** festgenagelt
- **Bewusste Kompromisse** (dokumentiert): der Schlüssel liegt in derselben Datenbank wie die verschlüsselten Daten (kein manuelles Schlüssel-Handling); `SMH_DISABLE_AUTH=1` schaltet den Login komplett ab

Verlauf der Sicherheitsupdates → [CHANGELOG.md](CHANGELOG.md) (Einträge mit 🔒).

<a id="de-tech-stack"></a>

### 🧱 Tech-Stack

| Teil | Technik |
|---|---|
| Backend | Python 3.12 · FastAPI · Uvicorn · requests · cryptography |
| Web | Jinja2 (serverseitig gerendert) · Vanilla-JS — kein Node-Build |
| Daten | SQLite (eigene Daten unter `/data`) · TMDb · TheTVDB |
| Deploy | Docker (gibt Root ab) · GHCR · Unraid |

<a id="de-entwicklung"></a>

### 🛠️ Entwicklung

```bash
pip install -r requirements.txt
cp .env.example .env         # Werte eintragen, DATA_DIR=./data
python -m app.main
```

**Tests:** eine automatische Test-Suite gibt es noch nicht.

<a id="de-roadmap"></a>

### 🗺️ Roadmap

- [x] Nur lesender Import aus Emby / Jellyfin / Plex in eine eigene DB
- [x] Cover- + Listenansicht, Technik-/Qualitätsanalyse, Abgleich mit TMDb + TheTVDB
- [x] Vollständigkeit je Staffel, Episoden-Reihenfolge Ausstrahlung / DVD / Absolut
- [x] Tag-System + Regel-Engine, Monitoring &amp; Benachrichtigungen
- [x] FSK-Qualitätskontrolle (portiert aus `emby-fsk-manager`), Sperr-Status, Drift-Erkennung
- [x] Quellenverwaltung in der Oberfläche: Liste + Anlegen/Bearbeiten-Dialog, verschlüsselte Zugangsdaten, Bibliotheks-Auswahl je Quelle, **mehrere Quellen desselben Typs**
- [x] Zweisprachige Oberfläche, optionaler Login, Update-Prüfung
- [ ] Filmreihen-/Sequel-Tracking

<p align="right"><a href="#-deutsch">⬆ nach oben</a></p>

---

<div align="center">

**SelfMediaHub** · part of the Self family · Teil der Self-Familie<br>
made with 🎬 for self-hosting

</div>
