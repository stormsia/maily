from __future__ import annotations

import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger("mailtmapi.crypto")


def is_fernet_key(secret: str) -> bool:
    if not secret:
        return False
    try:
        Fernet(secret.encode())
        return True
    except (ValueError, TypeError):
        return False


def _fernet(secret: str) -> Fernet:
    raw = secret.encode()
    try:
        return Fernet(raw)
    except (ValueError, TypeError):
        digest = hashlib.sha256(raw).digest()
        logger.warning(
            "secret is not a valid Fernet key; deriving a key via sha256(secret). "
            "This is deterministic, but prefer a Fernet key (cryptography.fernet.Fernet.generate_key())."
        )
        return Fernet(base64.urlsafe_b64encode(digest))


def encrypt(secret: str, plaintext: str) -> str:
    return _fernet(secret).encrypt(plaintext.encode()).decode()


def decrypt(secret: str, token: str) -> str:
    try:
        return _fernet(secret).decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("cannot decrypt value") from exc
