from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from cryptography.fernet import Fernet
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MAILTM_",
        env_file=".env",
        extra="ignore",
    )

    api_key: str = ""
    secret_key: str = ""
    database_url: str = "sqlite+aiosqlite:///mailtm.db"
    host: str = "127.0.0.1"
    port: int = 8477
    proxy: str | None = None
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_credentials_path: str = ""
    gmail_auth_uri: str = "https://accounts.google.com/o/oauth2/v2/auth"
    gmail_token_uri: str = "https://oauth2.googleapis.com/token"
    secret_key_path: Path = Field(default=Path("mailtm.key"))
    retention_interval_seconds: int = 60
    retention_interval_seconds: int = 60
    domain_cache_enabled: bool = True
    domain_cache_interval_seconds: int = 1800

    def resolved_secret_key(self) -> str:
        if self.secret_key:
            return self.secret_key
        if self.secret_key_path.exists():
            return self.secret_key_path.read_text(encoding="utf-8").strip()
        key = Fernet.generate_key().decode()
        self.secret_key_path.write_text(key, encoding="utf-8")
        return key

    def gmail_client(self) -> tuple[str, str]:
        if self.gmail_client_id and self.gmail_client_secret:
            return self.gmail_client_id, self.gmail_client_secret
        if self.gmail_credentials_path:
            raw = json.loads(Path(self.gmail_credentials_path).read_text(encoding="utf-8"))
            installed = raw.get("installed") or raw.get("web") or raw
            return installed["client_id"], installed["client_secret"]
        raise RuntimeError("Set MAILTM_GMAIL_CLIENT_ID/SECRET or MAILTM_GMAIL_CREDENTIALS_PATH")

    def gmail_redirect_uri(self) -> str:
        return f"http://{self.host}:{self.port}/v1/gmail/oauth/callback"


@lru_cache
def get_settings() -> Settings:
    return Settings()
