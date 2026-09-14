"""Account and Token schemas (Pydantic v2)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    token: str


class Account(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    address: str
    password: Optional[str] = None
    quota: int = 0
    used: int = 0
    isDisabled: bool = False
    isDeleted: bool = False
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    token: Token
