from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .base import MailProvider, ProviderCapabilities, TargetKind, get_capabilities


class ProviderRegistry:
    """Central registry of active MailProvider adapters."""

    def __init__(self, providers: list[MailProvider] | None = None) -> None:
        self._by_slug: dict[str, MailProvider] = {}
        for p in providers or []:
            self.register(p)

    def register(self, provider: MailProvider) -> None:
        """Register or replace a provider adapter."""
        if not getattr(provider, "slug", ""):
            raise ValueError(f"Provider {provider!r} must have a non-empty slug")
        self._by_slug[provider.slug] = provider

    def unregister(self, slug: str) -> MailProvider | None:
        """Remove a provider by slug. Returns the removed provider or None."""
        return self._by_slug.pop(slug, None)

    def get(self, slug: str) -> MailProvider:
        """Retrieve provider by slug, or raise KeyError."""
        try:
            return self._by_slug[slug]
        except KeyError as exc:
            raise KeyError(f"unknown provider {slug!r}") from exc

    def all(self) -> list[MailProvider]:
        """All registered provider adapters."""
        return list(self._by_slug.values())

    def slugs(self) -> list[str]:
        """List of registered provider slugs."""
        return list(self._by_slug)

    def by_kind(self, kind: TargetKind) -> list[MailProvider]:
        """Filter registered providers by target kind ('domain' or 'parent')."""
        return [p for p in self._by_slug.values() if p.kind == kind]

    def capabilities(self, slug: str) -> ProviderCapabilities:
        """Return capabilities for the given provider slug."""
        return get_capabilities(self.get(slug))

    def __contains__(self, slug: str) -> bool:
        return slug in self._by_slug

    def __iter__(self) -> Iterator[MailProvider]:
        return iter(self._by_slug.values())

    def __len__(self) -> int:
        return len(self._by_slug)

    def summary(self) -> list[dict[str, Any]]:
        """Return introspection metadata for all registered providers."""
        out: list[dict[str, Any]] = []
        for p in self._by_slug.values():
            caps = get_capabilities(p)
            out.append(
                {
                    "slug": p.slug,
                    "kind": p.kind,
                    "capabilities": {
                        "can_choose_username": caps.can_choose_username,
                        "can_choose_domain": caps.can_choose_domain,
                        "can_set_password": caps.can_set_password,
                        "supports_delete_mailbox": caps.supports_delete_mailbox,
                        "supports_delete_message": caps.supports_delete_message,
                        "supports_mark_read": caps.supports_mark_read,
                        "supports_source": caps.supports_source,
                        "supports_attachments": caps.supports_attachments,
                    },
                }
            )
        return out

    async def close(self) -> None:
        """Close all registered providers gracefully."""
        for p in self._by_slug.values():
            await p.close()


# Provider slugs that require pre-configured user credentials or private OAuth
# accounts and must be excluded from automated public health and e2e delivery tests.
EXCLUDED_LIVE_TEST_PROVIDERS: frozenset[str] = frozenset({"gmail"})


def create_public_providers(
    http: Any = None,
    settings: Any = None,
) -> list[MailProvider]:
    """Instantiate and return all public mail providers.

    All providers returned by this function are public disposable email services
    that support automated live health checks and E2E email delivery.
    """
    from .anonymmail_net import AnonymMailNet
    from .dispoemail_org import DispoEmailOrg
    from .mailtm import MailTM
    from .noopmail_org import NoopMail
    from .temp_tf import TempTF
    from .tempmail_io import TempMailIO
    from .tempmail_plus import TempMailPlus

    temp_tf_dot = getattr(settings, "temp_tf_gmail_dot", True) if settings else True
    temp_tf_plus = getattr(settings, "temp_tf_gmail_plus", True) if settings else True

    return [
        MailTM(http=http),
        TempMailPlus(http=http),
        TempMailIO(http=http),
        TempTF(http=http, gmail_dot=temp_tf_dot, gmail_plus=temp_tf_plus),
        AnonymMailNet(http=http),
        DispoEmailOrg(http=http),
        NoopMail(http=http),
    ]
