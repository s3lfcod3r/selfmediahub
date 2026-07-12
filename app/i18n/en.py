"""English string catalog. Keys mirror de.py exactly."""
STRINGS = {
    # -- Navigation / Topbar --
    "nav.aria": "Main navigation",
    "nav.overview": "Overview",
    "nav.tags": "Tags",
    "nav.rules": "Rules",
    "topbar.settings": "Settings",
    "topbar.theme": "Light/Dark",
    "topbar.theme_aria": "Toggle theme",
    "topbar.sync": "Re-scan",
    "topbar.logged_in": "Signed in",
    "topbar.logout": "Sign out",
    "topbar.instance_name": "Instance name",
    "topbar.version_current": "Version v{v} is up to date",
    "topbar.version_update": "New version {latest} available (installed v{current}) - see release notes",

    # -- Account setup (first start) --
    "setup.account_title": "Set up account",
    "setup.account_sub": "Create your account on first start. Sign-in is enabled afterwards.",
    "setup.username": "Username",
    "setup.password": "Password",
    "setup.password_min": "min. 8 characters",
    "setup.password_repeat": "Repeat password",
    "setup.email": "Email",
    "setup.language": "Language",
    "setup.submit": "Create account & sign in",
    "setup.err_username_short": "Username too short (at least 3 characters).",
    "setup.err_password_short": "Password too short (at least 8 characters).",
    "setup.err_password_mismatch": "The passwords do not match.",

    # -- Sign in --
    "login.title": "Sign in",
    "login.username": "Username",
    "login.password": "Password",
    "login.submit": "Sign in",
    "login.error_bad": "Username or password is incorrect.",

    # -- No-source page (setup.html) --
    "setup_src.title": "Almost there - connect a source",
    "setup_src.desc": ("SelfMediaHub reads your library read-only and stores everything in its own "
                       "database. Nothing is changed on your media server. Add your first data source "
                       "now in Settings (Emby, Jellyfin, Plex or local folders) - server address and "
                       "API key are stored encrypted."),
    "setup_src.button": "Set up data source",
    "setup_src.hint": "Then click “Re-scan” in the top right.",

    # -- Settings: General / UI language --
    "settings.ui_language": "UI language",
    "settings.ui_language_desc": "Language of the interface. Applies right after saving - the page reloads.",

    # -- Settings: page (hero + tabs) --
    "settings.label": "Settings",
    "settings.title": "Configuration",
    "settings.intro": "Central management of {app}. Areas are filled in step by step - what already works is marked.",
    "settings.nav_aria": "Settings areas",
    "settings.tab.general": "General",
    "settings.tab.account": "Account",
    "settings.tab.sources": "Data sources & libraries",
    "settings.tab.metadata": "Metadata services",
    "settings.tab.fsk": "Age ratings",
    "settings.tab.about": "About & updates",

    # -- Settings: general --
    "settings.general.title": "General settings",
    "settings.general.instance_name": "Instance name",
    "settings.general.instance_placeholder": "e.g. Living room, Home cinema, Server 1",
    "settings.general.instance_desc": "Shown at the top next to the logo - handy if you run several instances. Leave empty to hide.",
    "settings.general.primary_language": "Primary language",
    "settings.general.primary_language_desc": "The main language of this instance. It determines which language flag is shown on covers and in the detail view (audio & subtitles) - <strong>full</strong> (all episodes), <strong>partial</strong> (some) or <strong>none</strong>. Changing it recalculates immediately, no re-scan needed.",

    # -- Settings: account --
    "settings.account.title": "Account",
    "settings.account.username": "Username",
    "settings.account.email": "Email",
    "settings.account.password_change": "Change password",
    "settings.account.password_current": "Current password",
    "settings.account.password_new": "New password (min. 8 characters)",
    "settings.account.auth_required": "Require sign-in",
    "settings.account.auth_desc": "Default: on. To turn it off (local-only installs) you must confirm - <strong>without sign-in your media management is accessible unprotected.</strong> Forgot your password? Set <code>SMH_DISABLE_AUTH=1</code> on the container to bypass the login wall.",

    # -- Settings: data sources --
    "settings.sources.title": "Data sources & libraries",
    "settings.sources.intro": "Connect your media servers or local folders. Credentials are stored <strong>encrypted</strong>. {app} only reads - it never writes back (exception: age ratings, enabled separately). One source per type for now; per server you can choose which libraries are monitored (empty = all).",
    "settings.sources.loading": "Loading sources …",

    # -- Settings: metadata --
    "settings.metadata.title": "Metadata services",
    "settings.metadata.placeholder": "Coming here: multiple info sources (TMDb, TheTVDB, OMDb, AniDB …) with their own API credentials and a freely selectable order (priority) per media type - e.g. AniDB first for anime.",

    # -- Settings: age ratings --
    "settings.fsk.title": "Age ratings",
    "settings.fsk.enable": "Enable age-rating check",
    "settings.fsk.enable_desc": "When off, all rating elements disappear from the UI: the rating corner on covers, the rating filter, the “No rating” stat, plus rating info, editor and warnings in the detail view. The data is kept - turning it back on shows everything instantly, no re-scan needed.",
    "settings.fsk.placeholder": "Unifying international ratings (FSK / PEGI / USK / age label), setting a display preference and the rating cross-check across sources are coming in <strong>Phase 5</strong>.",

    # -- Settings: about & updates --
    "settings.about.title": "About & updates",
    "settings.about.installed_version": "Installed version",
    "settings.about.update_status": "Update status",
    "settings.about.status_available": "New version {latest} available.",
    "settings.about.status_current": "Up to date - v{current} is the latest version.",
    "settings.about.status_unchecked": "Not checked yet.",
    "settings.about.check_now": "Check now",
    "settings.about.open_release": "Open release notes",
    "settings.about.auto_desc": "Otherwise the check runs automatically in the background (at startup and once a day); the header shows green “up to date” or red “update available”.",

    # -- Language names (primary-language dropdown, detail, filter) --
    "langname.ger": "German",
    "langname.eng": "English",
    "langname.jpn": "Japanese",
    "langname.fre": "French",
    "langname.spa": "Spanish",
    "langname.ita": "Italian",
    "langname.kor": "Korean",
    "langname.rus": "Russian",
    "langname.tur": "Turkish",
    "langname.pol": "Polish",
    "langname.nld": "Dutch",
    "langname.por": "Portuguese",
    "langname.chi": "Chinese",
    "langname.ara": "Arabic",

    "settings.about.status_error": "Could not check (no connection / no release).",

    # -- Toasts / messages (settings.js) --
    "msg.saved": "Saved",
    "msg.failed_prefix": "Failed: ",
    "msg.username_saved": "Username saved",
    "msg.email_saved": "Email saved",
    "msg.password_changed": "Password changed",
    "msg.auth_on": "Sign-in enabled",
    "msg.auth_off": "Sign-in disabled",
    "msg.auth_confirm": "Really disable sign-in?\n\nWithout sign-in your media management is reachable unprotected by anyone who can open the page.",
    "msg.fsk_on": "Age-rating check enabled",
    "msg.fsk_off": "Age-rating check disabled",
    "msg.primary_lang_saved": "Primary language saved",
    "msg.checking_updates": "Checking for updates ...",
    "msg.update_available": "Update available: {latest}",
    "msg.up_to_date": "Everything up to date",
    "msg.check_failed": "Check failed",

    # -- Sources editor (settings.js) --
    "sources.kind.local": "Local folders",
    "sources.load_failed": "Sources could not be loaded.",
    "sources.active": "active",
    "sources.name": "Name",
    "sources.server_url": "Server URL",
    "sources.api_key": "API key / token",
    "sources.secret_keep": "•••••••• (leave empty = unchanged)",
    "sources.secret_enter": "Enter API key / token",
    "sources.libraries": "Monitored libraries",
    "sources.libraries_hint": "empty = all",
    "sources.test": "Test",
    "sources.libraries_btn": "Libraries",
    "sources.delete": "Delete",
    "sources.paths": "Paths",
    "sources.paths_hint": "one per line (inside the container)",
    "sources.delete_confirm": "Really delete this source?\n\nItems imported from this source are removed on the next re-scan.",
    "sources.deleted": "Source deleted",
    "sources.delete_failed": "Delete failed",
    "sources.testing": "Testing connection …",
    "sources.test_ok": "Connection OK ✓",
    "sources.error_prefix": "Error: ",
    "sources.test_failed": "Connection failed",
    "sources.loading_libs": "Loading libraries …",
    "sources.libs_failed": "Libraries could not be loaded",
    "sources.no_libs": "No libraries found.",
    "sources.err_no_url": "Server URL is missing",
    "sources.err_no_key": "API key / token is missing",
    "sources.err_no_path": "Enter at least one path",
    "sources.saving": "Saving …",
    "sources.saved": "Source saved",
    "sources.save_failed": "Save failed",

    # -- Shared terms --
    "common.optional": "optional",
    "common.save": "Save",
}
