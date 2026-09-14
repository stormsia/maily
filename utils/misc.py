"""Miscellaneous helpers for mailtmapi."""
from __future__ import annotations

import secrets
import string

# Alphabet for random local parts (lowercase + digits, URL-safe)
_ADDR_ALPHABET = string.ascii_lowercase + string.digits
_PASS_ALPHABET = string.ascii_letters + string.digits + "!@#$%^&*"


def random_string(length: int = 12) -> str:
    """Return a cryptographically secure random alphanumeric string."""
    return "".join(secrets.choice(_ADDR_ALPHABET) for _ in range(length))


def random_password(length: int = 16) -> str:
    """Return a cryptographically secure random password."""
    return "".join(secrets.choice(_PASS_ALPHABET) for _ in range(length))
