"""Symmetrische Verschluesselung fuer gespeicherte Zugangsdaten (Fernet).

Zugangsdaten von Datenquellen (API-Keys, Tokens) landen ab Phase 4 in der DB
und duerfen dort nicht im Klartext stehen. Der Schluessel wird beim ersten
Bedarf automatisch erzeugt und in ``app_meta`` abgelegt - genau wie das
Session-Secret der Authentifizierung. Kein manuelles Schluessel-Handling.
"""
from cryptography.fernet import Fernet, InvalidToken

from .. import db

_META_KEY = "sources_crypto_key"


def _fernet() -> Fernet:
    key = db.get_meta(_META_KEY)
    if not key:
        key = Fernet.generate_key().decode("ascii")
        db.set_meta(_META_KEY, key)
    return Fernet(key.encode("ascii"))


def encrypt(plaintext: str) -> str:
    """Klartext -> Token. Leerer Wert bleibt leer (kein Secret gesetzt)."""
    if not plaintext:
        return ""
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt(token: str) -> str:
    """Token -> Klartext. Bei ungueltigem/leerem Token: leerer String."""
    if not token:
        return ""
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken:
        return ""
