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

    # -- Gemeinsame Begriffe --
    "common.optional": "optional",
    "common.save": "Speichern",
}
