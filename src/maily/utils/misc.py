from __future__ import annotations

import secrets
import string

_ADDR = string.ascii_lowercase + string.digits
_PASS = string.ascii_letters + string.digits + "!@#$%^&*"


def random_string(length: int = 12) -> str:
    return "".join(secrets.choice(_ADDR) for _ in range(length))


def random_password(length: int = 16) -> str:
    return "".join(secrets.choice(_PASS) for _ in range(length))
