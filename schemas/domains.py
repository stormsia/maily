"""Domain schemas (Pydantic v2)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Domain(BaseModel):
    """A single mail domain offered by the provider."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    domain: str
    isActive: bool = True
    isPrivate: bool = False
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


class Domains(BaseModel):
    """Paginated list of domains (hydra:member envelope)."""

    model_config = ConfigDict(populate_by_name=True)

    hydra_member: list[Domain] = Field(alias="hydra:member")
    hydra_totalItems: int = Field(0, alias="hydra:totalItems")
