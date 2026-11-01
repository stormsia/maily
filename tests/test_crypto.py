from __future__ import annotations

import logging

import pytest
from cryptography.fernet import Fernet, InvalidToken

from mailtmapi.crypto import _fernet, decrypt, encrypt, is_fernet_key, logger


def _key() -> str:
    return Fernet.generate_key().decode()


def test_logger_name():
    assert logger.name == "mailtmapi.crypto"


def test_roundtrip_with_fernet_key():
    key = _key()
    assert decrypt(key, encrypt(key, "token-123")) == "token-123"


def test_simple_secret_is_reusable():
    token = encrypt("test-secret", "tok")
    # sha256-derived key is deterministic: any encryption roundtrip works
    assert decrypt("test-secret", token) == "tok"
    assert decrypt("test-secret", encrypt("test-secret", "another")) == "another"


def test_simple_secret_emits_warning(caplog):
    with caplog.at_level(logging.WARNING, logger="mailtmapi.crypto"):
        encrypt("not-a-fernet-key", "sample")
    assert (
        "secret is not a valid Fernet key; deriving a key via sha256(secret). "
        "This is deterministic, but prefer a Fernet key (cryptography.fernet.Fernet.generate_key())."
    ) in caplog.text


def test_wrong_secret_raises_valueerror():
    token = encrypt(_key(), "tok")
    with pytest.raises(ValueError, match=r"^cannot decrypt value$") as exc_info:
        decrypt(_key(), token)
    assert exc_info.value.__cause__ is not None
    assert isinstance(exc_info.value.__cause__, InvalidToken)


def test_garbage_token_raises_valueerror():
    key = _key()
    with pytest.raises(ValueError, match=r"^cannot decrypt value$") as exc_info:
        decrypt(key, "not-a-valid-token")
    assert exc_info.value.__cause__ is not None
    assert isinstance(exc_info.value.__cause__, InvalidToken)


def test_empty_plaintext_roundtrip():
    key = _key()
    assert decrypt(key, encrypt(key, "")) == ""


def test_is_fernet_key():
    assert is_fernet_key(_key()) is True
    assert is_fernet_key("test-secret") is False
    assert is_fernet_key("") is False


def test_fernet_direct_roundtrip():
    key = _key()
    f = _fernet(key)
    assert isinstance(f, Fernet)
    f_derived = _fernet("my-secret")
    assert isinstance(f_derived, Fernet)
