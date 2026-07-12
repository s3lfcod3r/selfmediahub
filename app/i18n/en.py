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

    # -- Shared terms --
    "common.optional": "optional",
    "common.save": "Save",
}
