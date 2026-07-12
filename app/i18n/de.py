"""Deutscher Sprachkatalog. Keys sind namespaced (<bereich>.<name>).

Interpolation ueber str.format: Platzhalter wie {latest} -> im Template/JS
mit .format(latest=...) fuellen.
"""
STRINGS = {
    # -- Navigation / Topbar --
    "nav.aria": "Hauptnavigation",
    "nav.overview": "Übersicht",
    "nav.tags": "Tags",
    "nav.rules": "Regeln",
    "topbar.settings": "Einstellungen",
    "topbar.theme": "Hell/Dunkel",
    "topbar.theme_aria": "Theme umschalten",
    "topbar.sync": "Neu einlesen",
    "topbar.logged_in": "Angemeldet",
    "topbar.logout": "Abmelden",
    "topbar.instance_name": "Instanzname",
    "topbar.version_current": "Version v{v} ist aktuell",
    "topbar.version_update": "Neue Version {latest} verfügbar (installiert v{current}) - zu den Release-Infos",

    # -- Konto einrichten (erster Start) --
    "setup.account_title": "Konto einrichten",
    "setup.account_sub": "Lege beim ersten Start dein Konto an. Danach ist die Anmeldung aktiv.",
    "setup.username": "Benutzername",
    "setup.password": "Passwort",
    "setup.password_min": "min. 8 Zeichen",
    "setup.password_repeat": "Passwort wiederholen",
    "setup.email": "E-Mail",
    "setup.language": "Sprache",
    "setup.submit": "Konto anlegen & anmelden",
    "setup.err_username_short": "Benutzername zu kurz (mindestens 3 Zeichen).",
    "setup.err_password_short": "Passwort zu kurz (mindestens 8 Zeichen).",
    "setup.err_password_mismatch": "Die Passwörter stimmen nicht überein.",

    # -- Anmelden --
    "login.title": "Anmelden",
    "login.username": "Benutzername",
    "login.password": "Passwort",
    "login.submit": "Anmelden",
    "login.error_bad": "Benutzername oder Passwort ist falsch.",

    # -- Quelle-fehlt-Seite (setup.html) --
    "setup_src.title": "Fast fertig - noch eine Quelle verbinden",
    "setup_src.desc": ("SelfMediaHub liest deine Mediathek nur lesend und speichert alles in seiner "
                       "eigenen Datenbank. An deinem Medienserver wird nichts veraendert. Lege jetzt "
                       "in den Einstellungen deine erste Datenquelle an (Emby, Jellyfin, Plex oder "
                       "lokale Ordner) - Server-Adresse und API-Schluessel werden verschluesselt gespeichert."),
    "setup_src.button": "Datenquelle einrichten",
    "setup_src.hint": "Danach oben rechts „Neu einlesen“ klicken.",

    # -- Einstellungen: Allgemein / UI-Sprache --
    "settings.ui_language": "UI-Sprache",
    "settings.ui_language_desc": ("Sprache der Oberflaeche. Wirkt sofort nach dem Speichern - die "
                                  "Seite wird neu geladen."),

    # -- Einstellungen: Seite (Hero + Tabs) --
    "settings.label": "Einstellungen",
    "settings.title": "Konfiguration",
    "settings.intro": "Zentrale Verwaltung von {app}. Die Bereiche werden schrittweise mit Leben gefüllt - was schon funktioniert, ist markiert.",
    "settings.nav_aria": "Einstellungs-Bereiche",
    "settings.tab.general": "Allgemein",
    "settings.tab.account": "Account",
    "settings.tab.sources": "Datenquellen & Bibliotheken",
    "settings.tab.metadata": "Metadatendienste",
    "settings.tab.fsk": "FSK & Altersfreigaben",
    "settings.tab.about": "Über & Updates",

    # -- Einstellungen: Allgemein --
    "settings.general.title": "Allgemeine Einstellungen",
    "settings.general.instance_name": "Instanzname",
    "settings.general.instance_placeholder": "z.B. Wohnzimmer, Heimkino, Server 1",
    "settings.general.instance_desc": "Wird oben in der Kopfzeile neben dem Logo angezeigt - praktisch, wenn du mehrere Instanzen betreibst. Leer lassen zum Ausblenden.",
    "settings.general.primary_language": "Primäre Sprache",
    "settings.general.primary_language_desc": "Die Hauptsprache dieser Instanz. Sie bestimmt, welche Sprach-Flagge auf Covern und im Detail gezeigt wird (Ton & Untertitel) - <strong>voll</strong> (alle Folgen), <strong>teilweise</strong> (einige) oder <strong>gar nicht</strong>. Beim Umstellen wird sofort neu berechnet, kein neuer Scan nötig.",

    # -- Einstellungen: Account --
    "settings.account.title": "Account",
    "settings.account.username": "Benutzername",
    "settings.account.email": "E-Mail",
    "settings.account.password_change": "Passwort ändern",
    "settings.account.password_current": "Aktuelles Passwort",
    "settings.account.password_new": "Neues Passwort (min. 8 Zeichen)",
    "settings.account.auth_required": "Anmeldung erforderlich",
    "settings.account.auth_desc": "Standard: an. Zum Abschalten (nur für rein lokale Installationen) musst du bestätigen - <strong>ohne Anmeldung ist deine Medienverwaltung ungeschützt zugänglich.</strong> Passwort vergessen? Am Container <code>SMH_DISABLE_AUTH=1</code> setzen, dann greift die Login-Wand nicht.",

    # -- Einstellungen: Datenquellen --
    "settings.sources.title": "Datenquellen & Bibliotheken",
    "settings.sources.intro": "Verbinde deine Medienserver oder lokale Ordner. Zugangsdaten werden <strong>verschlüsselt</strong> gespeichert. {app} liest nur - es schreibt nie zurück (Ausnahme: FSK, separat aktivierbar). Pro Typ ist aktuell eine Quelle möglich; je Server kannst du auswählen, welche Bibliotheken überwacht werden (leer = alle).",
    "settings.sources.loading": "Lade Quellen …",

    # -- Einstellungen: Metadaten --
    "settings.metadata.title": "Metadatendienste",
    "settings.metadata.placeholder": "Hier entstehen: mehrere Informationsquellen (TMDb, TheTVDB, OMDb, AniDB …) mit eigenen API-Zugangsdaten und einer frei wählbaren Reihenfolge (Priorisierung) je Medienart - z.B. AniDB zuerst für Anime.",

    # -- Einstellungen: FSK --
    "settings.fsk.title": "FSK & Altersfreigaben",
    "settings.fsk.enable": "FSK-Prüfung aktivieren",
    "settings.fsk.enable_desc": "Ist das Feature aus, verschwinden alle FSK-Elemente aus der Oberfläche: FSK-Ecke am Cover, Freigabe-Filter, die Kennzahl „Ohne Freigabe“, sowie FSK-Angaben, -Editor und Warnhinweise im Detailfenster. Die Daten bleiben gespeichert - beim Wieder-Einschalten ist alles sofort da, kein neuer Scan nötig.",
    "settings.fsk.placeholder": "Internationale Freigaben (FSK / PEGI / USK / Altersangabe) vereinheitlichen, eine Anzeigepräferenz festlegen und der FSK-Check zum Abgleich der Quellen kommen in <strong>Phase 5</strong>.",

    # -- Einstellungen: Über & Updates --
    "settings.about.title": "Über & Updates",
    "settings.about.installed_version": "Installierte Version",
    "settings.about.update_status": "Update-Status",
    "settings.about.status_available": "Neue Version {latest} verfügbar.",
    "settings.about.status_current": "Aktuell - v{current} ist die neueste Version.",
    "settings.about.status_unchecked": "Noch nicht geprüft.",
    "settings.about.check_now": "Jetzt prüfen",
    "settings.about.open_release": "Release-Infos öffnen",
    "settings.about.auto_desc": "Die Prüfung läuft sonst automatisch im Hintergrund (beim Start und einmal täglich); die Kopfzeile zeigt grün „aktuell“ bzw. rot „Update verfügbar“.",

    # -- Sprachnamen (Primaere-Sprache-Dropdown, Detail, Filter) --
    "langname.ger": "Deutsch",
    "langname.eng": "Englisch",
    "langname.jpn": "Japanisch",
    "langname.fre": "Französisch",
    "langname.spa": "Spanisch",
    "langname.ita": "Italienisch",
    "langname.kor": "Koreanisch",
    "langname.rus": "Russisch",
    "langname.tur": "Türkisch",
    "langname.pol": "Polnisch",
    "langname.nld": "Niederländisch",
    "langname.por": "Portugiesisch",
    "langname.chi": "Chinesisch",
    "langname.ara": "Arabisch",

    "settings.about.status_error": "Konnte nicht geprüft werden (keine Verbindung/kein Release).",

    # -- Toasts / Meldungen (settings.js) --
    "msg.saved": "Gespeichert",
    "msg.failed_prefix": "Fehlgeschlagen: ",
    "msg.username_saved": "Benutzername gespeichert",
    "msg.email_saved": "E-Mail gespeichert",
    "msg.password_changed": "Passwort geändert",
    "msg.auth_on": "Anmeldung aktiviert",
    "msg.auth_off": "Anmeldung deaktiviert",
    "msg.auth_confirm": "Anmeldung wirklich abschalten?\n\nOhne Anmeldung ist deine Medienverwaltung ungeschützt für jeden erreichbar, der die Seite aufrufen kann.",
    "msg.fsk_on": "FSK-Prüfung aktiviert",
    "msg.fsk_off": "FSK-Prüfung deaktiviert",
    "msg.primary_lang_saved": "Primäre Sprache gespeichert",
    "msg.checking_updates": "Prüfe auf Updates ...",
    "msg.update_available": "Update verfügbar: {latest}",
    "msg.up_to_date": "Alles aktuell",
    "msg.check_failed": "Prüfung fehlgeschlagen",

    # -- Quellen-Editor (settings.js) --
    "sources.kind.local": "Lokale Ordner",
    "sources.load_failed": "Quellen konnten nicht geladen werden.",
    "sources.active": "aktiv",
    "sources.name": "Name",
    "sources.server_url": "Server-URL",
    "sources.api_key": "API-Key / Token",
    "sources.secret_keep": "•••••••• (leer lassen = unverändert)",
    "sources.secret_enter": "API-Key / Token eingeben",
    "sources.libraries": "Überwachte Bibliotheken",
    "sources.libraries_hint": "leer = alle",
    "sources.test": "Testen",
    "sources.libraries_btn": "Bibliotheken",
    "sources.delete": "Löschen",
    "sources.paths": "Pfade",
    "sources.paths_hint": "einer pro Zeile (im Container)",
    "sources.delete_confirm": "Quelle wirklich löschen?\n\nDie eingelesenen Einträge dieser Quelle werden beim nächsten Einlesen entfernt.",
    "sources.deleted": "Quelle gelöscht",
    "sources.delete_failed": "Löschen fehlgeschlagen",
    "sources.testing": "Teste Verbindung …",
    "sources.test_ok": "Verbindung OK ✓",
    "sources.error_prefix": "Fehler: ",
    "sources.test_failed": "Verbindung fehlgeschlagen",
    "sources.loading_libs": "Lade Bibliotheken …",
    "sources.libs_failed": "Bibliotheken konnten nicht geladen werden",
    "sources.no_libs": "Keine Bibliotheken gefunden.",
    "sources.err_no_url": "Server-URL fehlt",
    "sources.err_no_key": "API-Key / Token fehlt",
    "sources.err_no_path": "Mindestens einen Pfad angeben",
    "sources.saving": "Speichere …",
    "sources.saved": "Quelle gespeichert",
    "sources.save_failed": "Speichern fehlgeschlagen",

    # -- Gemeinsame Begriffe --
    "common.optional": "optional",
    "common.save": "Speichern",
}
