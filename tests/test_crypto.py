from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from mailtmapi.crypto import decrypt, encrypt, is_fernet_key


def _key() -> str:
    return Fernet.generate_key().decode()


def test_roundtrip_with_fernet_key():
    key = _key()
    assert decrypt(key, encrypt(key, "token-123")) == "token-123"


def test_simple_secret_is_reusable():
    token = encrypt("test-secret", "tok")
    # sha256-derived key is deterministic: any encryption roundtrip works
    assert decrypt("test-secret", token) == "tok"
    assert decrypt("test-secret", encrypt("test-secret", "another")) == "another"


def test_wrong_secret_raises_valueerror():
    token = encrypt(_key(), "tok")
    with pytest.raises(ValueError, match="cannot decrypt"):
        decrypt(_key(), token)


def test_garbage_token_raises_valueerror():
    key = _key()
    with pytest.raises(ValueError, match="cannot decrypt"):
        decrypt(key, "not-a-valid-token")


def test_empty_plaintext_roundtrip():
    key = _key()
    assert decrypt(key, encrypt(key, "")) == ""


def test_is_fernet_key():
    assert is_fernet_key(_key()) is True
    assert is_fernet_key("test-secret") is False
    assert is_fernet_key("") is False
