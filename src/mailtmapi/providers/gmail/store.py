from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from mailtmapi.exceptions import MailNotFoundError


@dataclass
class GmailParent:
    id: int
    email: str
    refresh_token: str
    access_token: str | None = None
    access_expires_at: float | None = None  # unix ts
    send_as: list[str] = field(default_factory=list)  # full emails, no plus tags
    scopes: str = ""
    status: str = "active"


class GmailParentStore(Protocol):
    async def list_active(self) -> list[GmailParent]: ...
    async def list_all(self) -> list[GmailParent]: ...
    async def get(self, parent_id: int) -> GmailParent: ...
    async def get_by_email(self, email: str) -> GmailParent | None: ...
    async def update(self, parent: GmailParent) -> None: ...
    async def add(self, parent: GmailParent) -> GmailParent: ...
    async def delete(self, parent_id: int) -> None: ...


class MemoryGmailStore:
    def __init__(self) -> None:
        self._parents: dict[int, GmailParent] = {}
        self._next_id = 1

    async def list_active(self) -> list[GmailParent]:
        return [p for p in self._parents.values() if p.status == "active"]

    async def list_all(self) -> list[GmailParent]:
        return list(self._parents.values())

    async def get(self, parent_id: int) -> GmailParent:
        try:
            return self._parents[parent_id]
        except KeyError:
            raise MailNotFoundError(f"gmail parent {parent_id} not found") from None

    async def get_by_email(self, email: str) -> GmailParent | None:
        wanted = email.casefold()
        for parent in self._parents.values():
            if parent.email.casefold() == wanted:
                return parent
        return None

    async def delete(self, parent_id: int) -> None:
        self._parents.pop(parent_id, None)

    async def update(self, parent: GmailParent) -> None:
        self._parents[parent.id] = parent

    async def add(self, parent: GmailParent) -> GmailParent:
        if parent.id == 0:
            parent.id = self._next_id
            self._next_id += 1
        else:
            self._next_id = max(self._next_id, parent.id + 1)
        self._parents[parent.id] = parent
        return parent
