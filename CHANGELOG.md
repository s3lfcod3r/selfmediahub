# 📰 Changelog

Newest version first. Full release notes per version: [GitHub Releases](https://github.com/s3lfcod3r/selfmediahub/releases).
Neueste Version zuerst. Die ausführlichen Release-Notes je Version: [GitHub Releases](https://github.com/s3lfcod3r/selfmediahub/releases).

---

## 0.7.1 · Oct 2026
- 🇬🇧 Robustness fixes: the **primary video stream / media source** is picked reliably, invalid `PORT` / `SCAN_INTERVAL_HOURS` values fall back to defaults instead of crashing, usernames may contain a colon, **TheTVDB pagination** fixed, faster tag lookup in the detail view; the partial Emby write-back was reverted.
- 🇩🇪 Robustheits-Fixes: der **primäre Video-Stream / die Medienquelle** wird zuverlässig gewählt, ungültige `PORT`-/`SCAN_INTERVAL_HOURS`-Werte fallen auf den Standard zurück statt abzustürzen, Benutzernamen dürfen einen Doppelpunkt enthalten, **TheTVDB-Seitenabruf** korrigiert, schnellere Tag-Abfrage im Detail; das Teil-Update beim Schreiben nach Emby wurde zurückgenommen.

## 0.7.0 · Aug 2026 🔒
- 🇬🇧 Security update: **login throttling** (5 failed attempts per IP → 15 min lock), `X-Forwarded-For` only trusted from `SMH_TRUSTED_PROXIES`, `/api/health` reveals nothing without a session, neutral error messages, **pinned dependencies and actions**, app now runs **non-root** (`PUID`/`PGID`, default 99:100).
- 🇩🇪 Sicherheitsupdate: **Anmelde-Bremse** (5 Fehlversuche je IP → 15 Min. Sperre), `X-Forwarded-For` nur noch von `SMH_TRUSTED_PROXIES` geglaubt, `/api/health` verrät ohne Sitzung nichts mehr, neutrale Fehlermeldungen, **feste Versionen für Pakete und Actions**, die App läuft jetzt **ohne Root** (`PUID`/`PGID`, Standard 99:100).

## 0.6.2 · Aug 2026 🔒
- 🇬🇧 Security update: closed a **stored XSS** via media titles/paths in the embedded page JSON.
- 🇩🇪 Sicherheitsupdate: **Stored XSS** über Medientitel/-pfade im eingebetteten Seiten-JSON geschlossen.

## 0.6.1 · Aug 2026
- 🇬🇧 **Episode order** is chosen by season layout, not just by runtime.
- 🇩🇪 Die **Episoden-Reihenfolge** wird nach der Staffelaufteilung gewählt, nicht nur nach der Laufzeit.

## 0.6.0 · Aug 2026
- 🇬🇧 **Completeness** always gives a reliable statement — exact or approximate.
- 🇩🇪 Die **Vollständigkeit** liefert immer eine belastbare Aussage — genau oder grob.

## 0.5.9 · Aug 2026
- 🇬🇧 No gap count when the season layout differs between server and metadata.
- 🇩🇪 Keine Lückenzahl mehr bei abweichender Staffelaufteilung zwischen Server und Metadaten.

## 0.5.8 · Aug 2026
- 🇬🇧 **Completeness per season** instead of all-or-nothing.
- 🇩🇪 **Vollständigkeit je Staffel** statt alles-oder-nichts.

## 0.5.7 · Aug 2026
- 🇬🇧 Toolbar of the ratings page aligned with the rest of the UI.
- 🇩🇪 Werkzeugleiste der FSK-Seite an die übrige Oberfläche angeglichen.

## 0.5.6 · Aug 2026
- 🇬🇧 **Episode order Aired / DVD / Absolute** per series, built-in **TheTVDB project key** (masked), TheTVDB as primary season structure, **season traffic lights per season**, upcoming seasons hidden, **`LOG_LEVEL`** logging with login and error logs.
- 🇩🇪 **Episoden-Reihenfolge Ausstrahlung / DVD / Absolut** je Serie, eingebauter **TheTVDB-Projekt-Key** (maskiert), TheTVDB als primäre Staffelstruktur, **Staffel-Ampeln je Staffel**, kommende Staffeln ausgeblendet, Logging mit **`LOG_LEVEL`** inkl. Login- und Fehler-Logs.

## 0.5.5 · Jul 2026
- 🇬🇧 From 31 seasons on, season badges are grouped in **blocks of ten**; cover badges scale.
- 🇩🇪 Ab 31 Staffeln werden die Staffel-Badges in **Zehnerblöcken** gruppiert; Cover-Badges skalieren.

## 0.5.4 · Jul 2026
- 🇬🇧 Five season badges per row, flush across the full cover width.
- 🇩🇪 Fünf Staffel-Badges je Reihe, bündig über die volle Coverbreite.

## 0.5.3 · Jul 2026
- 🇬🇧 Season badges at full badge height, column grid, optical centring.
- 🇩🇪 Staffel-Badges in voller Badge-Höhe, Spaltenraster, optische Zentrierung.

## 0.5.2 · Jul 2026
- 🇬🇧 **Season badges** per series instead of a single completeness badge.
- 🇩🇪 **Staffel-Badges** je Serie statt eines einzelnen Vollständigkeits-Badges.

## 0.5.1 · Jul 2026
- 🇬🇧 Cover layout editor removed again; badges back on fixed positions.
- 🇩🇪 Cover-Layout-Editor wieder entfernt; Badges zurück auf festen Plätzen.

## 0.5.0 · Jul 2026
- 🇬🇧 Cover layout editor with overlay grid; the **local-folder source was removed**.
- 🇩🇪 Cover-Layout-Editor mit Overlay-Raster; die **Quelle „lokale Ordner“ wurde entfernt**.

## 0.4.6 · Jul 2026
- 🇬🇧 Bug-fix round for the age-rating module (6 fixes).
- 🇩🇪 Bugfix-Runde für das FSK-Modul (6 Fixes).

## 0.4.5 · Jul 2026
- 🇬🇧 **Drift detection** (audit) for age ratings.
- 🇩🇪 **Drift-Erkennung** (Audit) für Altersfreigaben.

## 0.4.4 · Jul 2026
- 🇬🇧 **Ratings page** with list, editor and filters.
- 🇩🇪 **FSK-Bearbeitungsseite** mit Liste, Editor und Filtern.

## 0.4.3 · Jul 2026
- 🇬🇧 Reads the **rating lock status** from Emby, cover traffic light and status board.
- 🇩🇪 Liest den **Sperr-Status** der Freigaben aus Emby, Cover-Ampel und Anzeigetafel.

## 0.4.2 · Jul 2026
- 🇬🇧 Rating normalisation/translation and **international suggestions**.
- 🇩🇪 Normalisierung/Übersetzung von Freigaben und **internationale Vorschläge**.

## 0.4.1 · Jul 2026
- 🇬🇧 Metadata services reduced to two fixed services (**TMDb** and **TheTVDB**).
- 🇩🇪 Metadatendienste auf zwei feste Dienste umgebaut (**TMDb** und **TheTVDB**).

## 0.4.0 · Jul 2026
- 🇬🇧 **Multi-provider chain** per media type, **TheTVDB** added.
- 🇩🇪 **Multi-Provider-Kette** je Medienart, **TheTVDB** hinzugefügt.

## 0.3.1 · Jul 2026
- 🇬🇧 Metadata intro text renders HTML correctly.
- 🇩🇪 Der Einleitungstext der Metadaten-Einstellungen zeigt HTML korrekt an.

## 0.3.0 · Jul 2026
- 🇬🇧 Metadata service management and **external IDs** (foundation).
- 🇩🇪 Verwaltung der Metadatendienste und **externe IDs** (Fundament).

## 0.2.7 · Jul 2026
- 🇬🇧 Top-bar icon buttons (settings/theme) exactly the same size.
- 🇩🇪 Icon-Buttons in der Kopfzeile (Einstellungen/Theme) exakt gleich groß.

## 0.2.6 · Jul 2026
- 🇬🇧 Close button in the series detail aligned like in the source dialog.
- 🇩🇪 Schließen-Kreuz im Serien-Detail bündig wie im Quellen-Dialog.

## 0.2.5 · Jul 2026
- 🇬🇧 **Orbitron** wordmark font self-hosted instead of Google Fonts; TMDb enrichment heals stuck series, season 0 no longer counts.
- 🇩🇪 Wortmarken-Schrift **Orbitron** selbstgehostet statt Google Fonts; TMDb-Abgleich repariert hängende Serien, Staffel 0 zählt nicht mehr.

## 0.2.4 · Jul 2026
- 🇬🇧 Data-source redesign (list + dialog) and **multiple sources of the same type**.
- 🇩🇪 Datenquellen neu gestaltet (Liste + Dialog) und **mehrere Quellen desselben Typs**.

## 0.2.3 · Jul 2026
- 🇬🇧 README documents the bilingual UI and login.
- 🇩🇪 README beschreibt die zweisprachige Oberfläche und den Login.

## 0.2.2 · Jul 2026
- 🇬🇧 More compact overview, wordmark font on login/registration.
- 🇩🇪 Kompaktere Übersicht, Wortmarken-Schrift auf Login/Registrierung.

## 0.2.1 · Jul 2026
- 🇬🇧 **Image proxy**, episodes stored in the DB, language coverage with 3-state flags, **single-account login**, **data sources in the DB with encrypted credentials**, **bilingual UI (DE/EN)**.
- 🇩🇪 **Bild-Proxy**, Episoden in der DB, Sprach-Abdeckung mit 3-Zustand-Flaggen, **Ein-Konto-Login**, **Datenquellen in der DB mit verschlüsselten Zugangsdaten**, **zweisprachige Oberfläche (DE/EN)**.

## 0.2.0 · Jul 2026
- 🇬🇧 First tagged release: read-only Emby/Jellyfin/Plex import, cover + list views, technical analysis, TMDb enrichment, completeness, tags + rule engine, monitoring, FSK quality control, settings page, **update check + automatic GitHub releases**, codec/audio/subtitle filters.
- 🇩🇪 Erste getaggte Version: read-only Import aus Emby/Jellyfin/Plex, Cover- + Listenansicht, Technik-Analyse, TMDb-Abgleich, Vollständigkeit, Tags + Regel-Engine, Monitoring, FSK-Qualitätskontrolle, Einstellungsseite, **Update-Prüfung + automatische GitHub-Releases**, Filter nach Codec/Audio/Untertitel.
