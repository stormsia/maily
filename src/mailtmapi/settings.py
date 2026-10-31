from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from pathlib import Path

from cryptography.fernet import Fernet
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("mailtmapi.settings")


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
    gmail_redirect_uri: str = ""
    secret_key_path: Path = Field(default=Path("mailtm.key"))
    retention_interval_seconds: int = 60
    db_maintenance_enabled: bool = True
    db_maintenance_interval_minutes: int = 60
    sqlite_busy_timeout_ms: int = 60000
    domain_cache_enabled: bool = True
    domain_cache_interval_seconds: int = 1800
    tempmail_io_origin: str = "https://temp-mail.io/"
    tempmail_io_cors_header: str = ""
    provider_headers_ttl_seconds: int = 21600
    temp_tf_gmail_dot: bool = True
    temp_tf_gmail_plus: bool = True

    def resolved_secret_key(self) -> str:
        """Encryption key, resolved once.

        Cached on the instance: a failed persist must not mint a new key on
        the next call, or tokens encrypted with the previous one become
        unreadable for the rest of the process.
        """
        cached = getattr(self, "_resolved_secret", None)
        if cached:
            return cached
        if self.secret_key:
            key = self.secret_key
        elif self.secret_key_path.exists():
            key = self.secret_key_path.read_text(encoding="utf-8").strip()
        else:
            key = Fernet.generate_key().decode()
            try:
                self.secret_key_path.write_text(key, encoding="utf-8")
                os.chmod(self.secret_key_path, 0o600)
            except OSError as exc:
                logger.warning("could not persist generated secret key to %s: %s", self.secret_key_path, exc)
            logger.warning(
                "generated a new encryption key at %s — keep this file safe and persisted "
                "across restarts, otherwise stored credentials cannot be decrypted",
                self.secret_key_path,
            )
        object.__setattr__(self, "_resolved_secret", key)
        return key

    def gmail_client(self) -> tuple[str, str]:
        if self.gmail_client_id and self.gmail_client_secret:
            return self.gmail_client_id, self.gmail_client_secret
        if self.gmail_credentials_path:
            raw = json.loads(Path(self.gmail_credentials_path).read_text(encoding="utf-8"))
            installed = raw.get("installed") or raw.get("web") or raw
            return installed["client_id"], installed["client_secret"]
        raise RuntimeError("Set MAILTM_GMAIL_CLIENT_ID/SECRET or MAILTM_GMAIL_CREDENTIALS_PATH")

    def default_gmail_redirect_uri(self) -> str:
        return self.gmail_redirect_uri or f"http://{self.host}:{self.port}/v1/gmail/oauth/callback"


@lru_cache
def get_settings() -> Settings:
    return Settings()
