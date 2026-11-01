"""Data models for test email sending operations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class AttemptInfo:
    """Diagnostic details of a single provider attempt."""

    provider: str
    success: bool
    status_code: int | None = None
    error: str | None = None
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EmailSendResult:
    """Result of sending a test email to a target address."""

    email: str
    success: bool
    provider: str
    fallback_used: bool = False
    message_id: str | None = None
    detail: str = ""
    duration_ms: float = 0.0
    attempts: list[AttemptInfo] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
