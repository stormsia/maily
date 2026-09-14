from __future__ import annotations

from .base import MailProvider


class ProviderRegistry:
    def __init__(self, providers: list[MailProvider]) -> None:
        self._by_slug: dict[str, MailProvider] = {p.slug: p for p in providers}

    def get(self, slug: str) -> MailProvider:
        try:
            return self._by_slug[slug]
        except KeyError as exc:
            raise KeyError(f"unknown provider {slug!r}") from exc

    def all(self) -> list[MailProvider]:
        return list(self._by_slug.values())

    def slugs(self) -> list[str]:
        return list(self._by_slug)

    async def close(self) -> None:
        for p in self._by_slug.values():
            await p.close()
