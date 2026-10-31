from __future__ import annotations

import string

from mailtmapi.utils.misc import _ADDR, _PASS, random_password, random_string


def test_constants():
    expected_addr = string.ascii_lowercase + string.digits
    expected_pass = string.ascii_letters + string.digits + "!@#$%^&*"
    assert expected_addr == _ADDR
    assert expected_pass == _PASS


def test_random_string_default_length():
    res = random_string()
    assert len(res) == 12
    assert all(c in _ADDR for c in res)


def test_random_string_custom_lengths():
    assert random_string(0) == ""
    assert len(random_string(1)) == 1
    assert len(random_string(32)) == 32
    res = random_string(50)
    assert len(res) == 50
    assert all(c in _ADDR for c in res)


def test_random_string_uniqueness_and_distribution():
    strings = {random_string(16) for _ in range(50)}
    # All 50 should be distinct
    assert len(strings) == 50

    # Across multiple generations, both lowercase letters and digits must appear
    combined = "".join(random_string(20) for _ in range(20))
    has_alpha = any(c in string.ascii_lowercase for c in combined)
    has_digit = any(c in string.digits for c in combined)
    assert has_alpha and has_digit


def test_random_password_default_length():
    res = random_password()
    assert len(res) == 16
    assert all(c in _PASS for c in res)


def test_random_password_custom_lengths():
    assert random_password(0) == ""
    assert len(random_password(1)) == 1
    assert len(random_password(64)) == 64
    res = random_password(100)
    assert len(res) == 100
    assert all(c in _PASS for c in res)


def test_random_password_uniqueness_and_character_classes():
    passwords = {random_password(24) for _ in range(50)}
    assert len(passwords) == 50

    # Over several random passwords, ensure letters, digits, and punctuation occur
    combined = "".join(random_password(30) for _ in range(30))
    has_alpha = any(c in string.ascii_letters for c in combined)
    has_digit = any(c in string.digits for c in combined)
    has_special = any(c in "!@#$%^&*" for c in combined)
    assert has_alpha and has_digit and has_special
