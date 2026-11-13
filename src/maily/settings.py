from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet
from loguru import logger
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

#: Public PostHog project token of the "Maily" project (US region). It is an
#: ingest token (``phc_...``), not a personal API key, so it ships with the
#: release. Forks that point at their own project override the
#: ``telemetry_posthog_api_key`` setting.
POSTHOG_PROJECT_TOKEN = "phc_sr8WfrC9Bb75YodHpdDzK7DRwLAddWNcfNovGimMLoGC"

#: Sentinel for forks that have no PostHog project yet. While it is
#: configured the telemetry module stays inactive and never opens a network
#: connection.
POSTHOG_PLACEHOLDER_TOKEN = "phc_REPLACE_WITH_REAL_PROJECT_TOKEN"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MAILY_",
        env_file=".env",
        extra="ignore",
    )

    api_key: str = ""
    secret_key: str = ""
    database_url: str = "sqlite+aiosqlite:///maily.db"
    host: str = "127.0.0.1"
    port: int = 8477
    proxy: str | None = None
    telemetry_proxy: str | None = None

    # Telemetry is opt-out via MAILY_TELEMETRY_ENABLED=false. The PostHog
    # project token is baked into the settings above; the matching environment
    # variable only exists to point a fork at a different project.
    telemetry_enabled: bool = True
    telemetry_posthog_api_key: str = POSTHOG_PROJECT_TOKEN
    telemetry_posthog_host: str = "https://us.i.posthog.com"
    telemetry_include_ip: bool = True
    telemetry_geo_lookup_enabled: bool = True
    telemetry_geo_lookup_url: str = "https://ipwho.is/"
    telemetry_daily_hour_utc: int = 4
    telemetry_daily_jitter_seconds: int = 900
    telemetry_immediate_debounce_seconds: float = 2.0
    telemetry_app_start_debounce_seconds: int = 300
    telemetry_http_timeout_seconds: float = 10.0
    telemetry_max_attempts: int = 8
    telemetry_queue_maxsize: int = 512
    telemetry_max_batch_events: int = 50
    telemetry_max_event_bytes: int = 900_000
    telemetry_sent_retention_days: int = 7
    telemetry_unsent_retention_days: int = 30
    telemetry_person_profiles: bool = True

    @field_validator("proxy", "telemetry_proxy", mode="before")
    @classmethod
    def _sanitize_proxy(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.strip():
            return None
        return v

    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_credentials_path: str = ""
    gmail_auth_uri: str = "https://accounts.google.com/o/oauth2/v2/auth"
    gmail_token_uri: str = "https://oauth2.googleapis.com/token"
    gmail_redirect_uri: str = ""
    secret_key_path: Path = Field(default=Path("maily.key"))
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
                logger.warning(
                    "could not persist generated secret key to %s: %s", self.secret_key_path, exc
                )
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
        raise RuntimeError("Set MAILY_GMAIL_CLIENT_ID/SECRET or MAILY_GMAIL_CREDENTIALS_PATH")

    def default_gmail_redirect_uri(self) -> str:
        if self.gmail_redirect_uri:
            return self.gmail_redirect_uri.replace("://0.0.0.0", "://127.0.0.1")
        host = "127.0.0.1" if self.host in ("0.0.0.0", "::", "") else self.host
        port = self.port or 8477
        return f"http://{host}:{port}/v1/gmail/oauth/callback"


@lru_cache
def get_settings() -> Settings:
    return Settings()
