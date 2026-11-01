from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from hypothesis import given
from hypothesis import strategies as st

from mailtmapi.app.authz import (
    Principal,
    _deny_scope,
    _expired,
    _forbidden,
    _invalid_api_key,
    _is_root_secret,
    action_allowed,
    owns_mailbox,
    parent_allowed,
    parse_scope,
    presented_secret,
    provider_allowed,
    secret_sha256,
)
from mailtmapi.db.models import ApiKey, Mailbox

# --- Hypothesis Property Tests ---


@given(st.text())
def test_property_secret_sha256_matches_hashlib(secret: str):
    """SHA-256 digest must strictly match hashlib hex digest for any string."""
    expected = hashlib.sha256(secret.encode()).hexdigest()
    assert secret_sha256(secret) == expected
    assert len(secret_sha256(secret)) == 64


@given(st.text(), st.text())
def test_property_is_root_secret(presented: str, expected: str):
    """Only non-empty matching secrets yield root access."""
    res = _is_root_secret(presented, expected)
    if not presented or not expected:
        assert res is False
    elif presented == expected:
        assert res is True
    else:
        assert res is False


@given(
    st.one_of(st.none(), st.text()),
    st.one_of(st.none(), st.text()),
)
def test_property_presented_secret_priority(x_api_key: str | None, auth_header: str | None):
    """X-API-Key always takes precedence over Authorization header."""
    res = presented_secret(x_api_key, auth_header)
    if x_api_key:
        assert res == x_api_key
    elif auth_header is None or not auth_header.lower().startswith("bearer "):
        assert res is None
    else:
        token = auth_header[7:].strip()
        assert res == (token if token else None)


@given(st.text())
def test_property_parse_scope_arbitrary_json_never_crashes(payload: str):
    """Arbitrary string or corrupted JSON never raises an unhandled exception."""
    scope = parse_scope(payload)
    assert isinstance(scope.providers, tuple)
    assert isinstance(scope.parent_ids, tuple)
    assert isinstance(scope.actions, frozenset)
    assert isinstance(scope.providers_open, bool)


# --- Strict Invariant & Mutant-Killing Tests ---


def test_invalid_api_key_exception_structure():
    """Verify HTTP 401 exception exact status, detail, and headers."""
    exc = _invalid_api_key()
    assert exc.status_code == 401
    assert exc.detail == "invalid api key"
    assert exc.headers == {"X-MailTM-Error": "api_key"}


def test_forbidden_exception_structure():
    """Verify HTTP 403 exception exact status and detail."""
    exc = _forbidden()
    assert exc.status_code == 403
    assert exc.detail == "forbidden"
    assert exc.headers is None


def test_deny_scope_invariants():
    """Verify deny scope is completely closed to all operations."""
    deny = _deny_scope()
    assert deny.providers == ()
    assert deny.parent_ids == ()
    assert deny.actions == frozenset()
    assert deny.providers_open is False


def test_parse_scope_malformed_types():
    """Verify all non-list and non-string payload variants fall back to deny."""
    assert parse_scope("null") == _deny_scope()
    assert parse_scope("[]") == _deny_scope()
    assert parse_scope('{"providers": "mail.tm"}') == _deny_scope()
    assert (
        parse_scope('{"providers": ["mail.tm"], "parent_ids": "not_list", "actions": []}')
        == _deny_scope()
    )
    assert parse_scope('{"providers": [123], "parent_ids": [], "actions": []}') == _deny_scope()
    assert (
        parse_scope('{"providers": [], "parent_ids": ["not_int"], "actions": []}') == _deny_scope()
    )
    assert parse_scope('{"providers": [], "parent_ids": [], "actions": [123]}') == _deny_scope()


def test_expiry_boundary_conditions():
    """Verify expires_at <= now condition."""
    now = datetime(2026, 11, 1, 12, 0, 0, tzinfo=timezone.utc).replace(tzinfo=None)
    key_never = ApiKey(
        id=1,
        name="k",
        prefix="p",
        secret_enc="e",
        secret_sha256="s",
        scope_json="{}",
        expires_at=None,
    )
    key_future = ApiKey(
        id=2,
        name="k",
        prefix="p",
        secret_enc="e",
        secret_sha256="s",
        scope_json="{}",
        expires_at=datetime(2026, 11, 1, 12, 0, 1),
    )
    key_exact = ApiKey(
        id=3,
        name="k",
        prefix="p",
        secret_enc="e",
        secret_sha256="s",
        scope_json="{}",
        expires_at=now,
    )
    key_past = ApiKey(
        id=4,
        name="k",
        prefix="p",
        secret_enc="e",
        secret_sha256="s",
        scope_json="{}",
        expires_at=datetime(2026, 11, 1, 11, 59, 59),
    )

    assert _expired(key_never, now) is False
    assert _expired(key_future, now) is False
    assert _expired(key_exact, now) is True
    assert _expired(key_past, now) is True


def test_action_allowed_root_and_issued():
    root = Principal(is_root=True, key=None)
    assert action_allowed(root, "mailboxes:read", "messages:write", "custom:action") is True

    anon = Principal(is_root=False, key=None)
    assert action_allowed(anon, "mailboxes:read") is False

    key = ApiKey(
        id=1,
        name="k",
        prefix="p",
        secret_enc="e",
        secret_sha256="s",
        scope_json=json.dumps(
            {
                "providers": ["mail.tm"],
                "parent_ids": [],
                "actions": ["mailboxes:read", "messages:read"],
            }
        ),
    )
    p = Principal(is_root=False, key=key)
    assert action_allowed(p, "mailboxes:read") is True
    assert action_allowed(p, "messages:read") is True
    assert action_allowed(p, "mailboxes:read", "messages:read") is True
    assert action_allowed(p, "mailboxes:write") is False
    assert action_allowed(p, "mailboxes:read", "mailboxes:write") is False


def test_provider_allowed_open_and_restricted():
    root = Principal(is_root=True, key=None)
    assert provider_allowed(root, "any-provider") is True

    anon = Principal(is_root=False, key=None)
    assert provider_allowed(anon, "mail.tm") is False

    # Open providers
    key_open = ApiKey(
        id=1,
        name="k",
        prefix="p",
        secret_enc="e",
        secret_sha256="s",
        scope_json=json.dumps({"providers": [], "parent_ids": [], "actions": ["mailboxes:read"]}),
    )
    p_open = Principal(is_root=False, key=key_open)
    assert provider_allowed(p_open, "mail.tm") is True
    assert provider_allowed(p_open, "tempmail.plus") is True

    # Restricted providers
    key_res = ApiKey(
        id=2,
        name="k",
        prefix="p",
        secret_enc="e",
        secret_sha256="s",
        scope_json=json.dumps(
            {"providers": ["mail.tm"], "parent_ids": [], "actions": ["mailboxes:read"]}
        ),
    )
    p_res = Principal(is_root=False, key=key_res)
    assert provider_allowed(p_res, "mail.tm") is True
    assert provider_allowed(p_res, "tempmail.plus") is False


def test_parent_allowed_root_and_issued():
    root = Principal(is_root=True, key=None)
    assert parent_allowed(root, 123) is True

    anon = Principal(is_root=False, key=None)
    assert parent_allowed(anon, 123) is False

    key = ApiKey(
        id=1,
        name="k",
        prefix="p",
        secret_enc="e",
        secret_sha256="s",
        scope_json=json.dumps({"providers": [], "parent_ids": [10, 20], "actions": []}),
    )
    p = Principal(is_root=False, key=key)
    assert parent_allowed(p, 10) is True
    assert parent_allowed(p, 20) is True
    assert parent_allowed(p, 30) is False


def test_owns_mailbox_rules():
    """Verify ownership rules for root, key owner, and foreign key."""
    root = Principal(is_root=True, key=None)
    key1 = ApiKey(id=1, name="k1", prefix="p", secret_enc="e", secret_sha256="s", scope_json="{}")
    key2 = ApiKey(id=2, name="k2", prefix="p", secret_enc="e", secret_sha256="s", scope_json="{}")
    p1 = Principal(is_root=False, key=key1)
    p2 = Principal(is_root=False, key=key2)
    p_none = Principal(is_root=False, key=None)

    box_owned_1 = Mailbox(id=1, provider="mail.tm", address="a@b.com", owner_key_id=1)
    box_unowned = Mailbox(id=2, provider="mail.tm", address="c@d.com", owner_key_id=None)

    assert owns_mailbox(root, box_owned_1) is True
    assert owns_mailbox(root, box_unowned) is True
    assert owns_mailbox(p1, box_owned_1) is True
    assert owns_mailbox(p2, box_owned_1) is False
    assert owns_mailbox(p1, box_unowned) is False
    assert owns_mailbox(p_none, box_owned_1) is False
