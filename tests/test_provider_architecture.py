from __future__ import annotations

import pytest

from mailtmapi.providers.base import (
    HttpProvider,
    MailboxInfo,
    ProviderCapabilities,
    get_capabilities,
    split_address,
)
from mailtmapi.providers.registry import ProviderRegistry
from tests.helpers import StubProvider


def test_split_address():
    user, domain = split_address("alice@example.com")
    assert user == "alice"
    assert domain == "example.com"

    with pytest.raises(ValueError):
        split_address("invalid-email")

    with pytest.raises(ValueError):
        split_address("@example.com")

    with pytest.raises(ValueError):
        split_address("alice@")


def test_provider_capabilities_defaults():
    caps = ProviderCapabilities()
    assert caps.can_choose_username is True
    assert caps.can_choose_domain is True
    assert caps.can_set_password is False
    assert caps.supports_delete_mailbox is True
    assert caps.supports_delete_message is True
    assert caps.supports_mark_read is False


def test_get_capabilities():
    p1 = StubProvider("stub1")
    caps1 = get_capabilities(p1)
    assert isinstance(caps1, ProviderCapabilities)

    class CustomProvider:
        slug = "custom"
        kind = "domain"
        capabilities = ProviderCapabilities(can_set_password=True, supports_mark_read=True)

    caps2 = get_capabilities(CustomProvider())
    assert caps2.can_set_password is True
    assert caps2.supports_mark_read is True


def test_provider_registry_advanced():
    reg = ProviderRegistry()
    assert len(reg) == 0

    p_domain = StubProvider("dom1")
    p_domain.kind = "domain"
    p_parent = StubProvider("par1")
    p_parent.kind = "parent"

    reg.register(p_domain)
    reg.register(p_parent)

    assert len(reg) == 2
    assert "dom1" in reg
    assert "par1" in reg
    assert "unknown" not in reg

    domain_provs = reg.by_kind("domain")
    assert len(domain_provs) == 1
    assert domain_provs[0].slug == "dom1"

    parent_provs = reg.by_kind("parent")
    assert len(parent_provs) == 1
    assert parent_provs[0].slug == "par1"

    caps = reg.capabilities("dom1")
    assert isinstance(caps, ProviderCapabilities)

    summary = reg.summary()
    assert len(summary) == 2
    slugs = [s["slug"] for s in summary]
    assert "dom1" in slugs
    assert "par1" in slugs

    removed = reg.unregister("dom1")
    assert removed is p_domain
    assert "dom1" not in reg
    assert len(reg) == 1


@pytest.mark.asyncio
async def test_http_provider_defaults():
    class MinimalHttpProvider(HttpProvider):
        slug = "mini"

        async def _fetch_targets(self, *, known=None):
            return []

    p = MinimalHttpProvider()
    try:
        box = MailboxInfo(provider="mini", address="u@d.com", token="tok")
        assert await p.delete_mailbox(box) is True
        assert await p.mark_read(box, "msg1") is True
    finally:
        await p.close()
