"""Ein-Konto-Authentifizierung (Single-User).

- Passwort: PBKDF2-HMAC-SHA256 (Standardbibliothek, keine Zusatz-Abhaengigkeit).
- Sitzung: signiertes Cookie (HMAC-SHA256 mit einem in app_meta erzeugten
  Server-Secret; das Passwort steckt NIE im Cookie).
- Notausgang: ENV SMH_DISABLE_AUTH bruecken (siehe config.DISABLE_AUTH).

Die API-Key-Verschluesselung kommt spaeter (Phase 4), wenn Quellen-Zugangsdaten
in die DB wandern.
"""
import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timezone

from .. import config, db

_PBKDF2_ITER = 240_000
_SESSION_MAX_AGE = 30 * 24 * 3600  # 30 Tage
SESSION_COOKIE = "smh_session"


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())


# -- Passwort ---------------------------------------------------------------
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITER)
    return f"pbkdf2_sha256${_PBKDF2_ITER}${_b64(salt)}${_b64(dk)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algo, iters, salt_b64, hash_b64 = encoded.split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), _unb64(salt_b64), int(iters))
        return hmac.compare_digest(dk, _unb64(hash_b64))
    except (ValueError, TypeError):
        return False


# -- Konto ------------------------------------------------------------------
def _row():
    rows = db.query("SELECT * FROM account WHERE id=1")
    return dict(rows[0]) if rows else None


def account_exists() -> bool:
    return bool(db.query("SELECT 1 FROM account WHERE id=1"))


def get_account() -> dict:
    row = _row()
    return None if row is None else {
        "username": row["username"], "email": row["email"] or "",
        "auth_enabled": bool(row["auth_enabled"]),
    }


def create_account(username: str, password: str, email: str = "") -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    db.execute(
        "INSERT INTO account (id, username, pw_hash, email, auth_enabled, created_at) "
        "VALUES (1, ?, ?, ?, 1, ?)",
        (username, hash_password(password), email or "", now),
    )


def verify_login(username: str, password: str) -> bool:
    row = _row()
    return bool(row and username == row["username"] and verify_password(password, row["pw_hash"]))


def set_username(username: str) -> None:
    db.execute("UPDATE account SET username=? WHERE id=1", (username,))


def set_email(email: str) -> None:
    db.execute("UPDATE account SET email=? WHERE id=1", (email or "",))


def set_password(new_password: str) -> None:
    db.execute("UPDATE account SET pw_hash=? WHERE id=1", (hash_password(new_password),))


def set_auth_enabled(enabled: bool) -> None:
    db.execute("UPDATE account SET auth_enabled=? WHERE id=1", (1 if enabled else 0,))


def auth_enabled() -> bool:
    row = _row()
    return bool(row and row["auth_enabled"])


def auth_active() -> bool:
    """Ist eine Anmeldung noetig? (Konto vorhanden, Auth an, Notausgang nicht gesetzt)."""
    if config.DISABLE_AUTH:
        return False
    return account_exists() and auth_enabled()


# -- Sitzung (signiertes Cookie) --------------------------------------------
def _secret() -> bytes:
    sec = db.get_meta("session_secret")
    if not sec:
        sec = secrets.token_hex(32)
        db.set_meta("session_secret", sec)
    return sec.encode("ascii")


def _sign(payload: str) -> str:
    return hmac.new(_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def make_session(username: str) -> str:
    payload = f"{username}:{_now_ts()}"
    return _b64(payload.encode("utf-8")) + "." + _sign(payload)


def verify_session(token: str) -> bool:
    if not token or "." not in token:
        return False
    try:
        payload_b64, sig = token.rsplit(".", 1)
        payload = _unb64(payload_b64).decode("utf-8")
    except (ValueError, TypeError):
        return False
    if not hmac.compare_digest(_sign(payload), sig):
        return False
    try:
        _username, issued = payload.split(":")
    except ValueError:
        return False
    if _now_ts() - int(issued) > _SESSION_MAX_AGE:
        return False
    # Single-User: gueltige Signatur + nicht abgelaufen + Konto existiert = angemeldet.
    # (Name im Token ist nur informativ - Umbenennen darf die Sitzung nicht killen.)
    return account_exists()
