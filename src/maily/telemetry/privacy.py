"""Property sanitization and privacy helpers.

Nothing in this module is allowed to raise: telemetry must never break a
request path. Values that cannot be represented safely are dropped or
truncated.
"""

from __future__ import annotations

import json
import os
import platform
import re
from collections.abc import Mapping
from datetime import date, datetime, timezone
from typing import Any

from .models import TelemetryState

# Keys whose names suggest personal or secret material. We match both snake_case
# and camelCase variants (e.g. email, userEmail, token, accessToken).
_SENSITIVE_KEY_RE = re.compile(
    r"(^|[a-z0-9]_|(?<=[a-z]))(address|email|subject|body|token|secret|password|refresh)(_|[A-Z]|$)|(^|_)api_key$|apiKey$",
    re.IGNORECASE,
)
_MAX_STRING = 512
_MAX_LIST = 100
_MAX_DICT = 200
_MAX_DEPTH = 4
_MAX_ERROR = 300


def sanitize_properties(properties: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return a JSON-safe copy with sensitive keys and oversized values removed."""
    if not properties:
        return {}
    out: dict[str, Any] = {}
    for key, value in properties.items():
        if not isinstance(key, str) or not key:
            continue
        if _SENSITIVE_KEY_RE.search(key):
            continue
        out[key] = _sanitize_value(value, depth=0)
    return out


def _sanitize_value(value: Any, *, depth: int) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value[:_MAX_STRING]
    if depth >= _MAX_DEPTH:
        return str(value)[:_MAX_STRING]
    if isinstance(value, (list, tuple)):
        return [_sanitize_value(item, depth=depth + 1) for item in value[:_MAX_LIST]]
    if isinstance(value, dict):
        return {
            str(key)[:128]: _sanitize_value(item, depth=depth + 1)
            for key, item in list(value.items())[:_MAX_DICT]
        }
    return str(value)[:_MAX_STRING]


def truncate_error(error: Any) -> str:
    """Collapse an exception/HTTP body into a short single-line string."""
    if error is None:
        return ""
    text = " ".join(str(error).split())
    if len(text) <= _MAX_ERROR:
        return text
    return text[: _MAX_ERROR - 1] + "…"


def json_bytes(value: Any) -> int:
    try:
        return len(json.dumps(value, default=str, separators=(",", ":")).encode("utf-8"))
    except (TypeError, ValueError):
        return 0


def deployment() -> str:
    if os.environ.get("KUBERNETES_SERVICE_HOST"):
        return "kubernetes"
    if os.environ.get("CONTAINER") or os.path.exists("/.dockerenv"):
        return "docker"
    return "bare"


def runtime_properties(settings: Any, version: str) -> dict[str, Any]:
    """Non-secret runtime facts included in every event."""
    gmail_env = bool(
        getattr(settings, "gmail_client_id", "") and getattr(settings, "gmail_client_secret", "")
    )
    return {
        "version": version,
        "python_version": platform.python_version(),
        "platform_system": platform.system().lower(),
        "platform_release": platform.release(),
        "platform_machine": platform.machine(),
        "cpu_count": os.cpu_count(),
        "deployment": deployment(),
        "api_key_required": bool(getattr(settings, "api_key", "")),
        "proxy_configured": bool(getattr(settings, "proxy", "")),
        "gmail_configured": gmail_env,
        "domain_cache_enabled": bool(getattr(settings, "domain_cache_enabled", False)),
        "db_maintenance_enabled": bool(getattr(settings, "db_maintenance_enabled", False)),
        "retention_interval_seconds": int(getattr(settings, "retention_interval_seconds", 0) or 0),
    }


def installation_properties(state: TelemetryState, today: date) -> dict[str, Any]:
    props: dict[str, Any] = {
        "installation_id": state.installation_id,
        "app_start_count": state.app_start_count,
        "first_version": state.first_version,
        "last_version": state.last_version,
    }
    if state.created_at is not None:
        props["install_age_days"] = max(0, (today - state.created_at.date()).days)
    if state.last_snapshot_day is not None:
        props["days_since_last_snapshot"] = max(0, (today - state.last_snapshot_day).days)
    if state.setup_completed_at is not None:
        props["setup_completed"] = True
    return props


def geo_properties(geo: Any | None, *, include_ip: bool) -> dict[str, Any]:
    """Geo fields for event properties. Empty/disabled geo disables PostHog GeoIP."""
    if not include_ip:
        return {"$geoip_disable": True}
    if geo is None:
        return {}
    props: dict[str, Any] = {
        "$ip": geo.ip,
        "country": geo.country,
        "country_code": geo.country_code,
        "region": geo.region,
        "city": geo.city,
        "geo_timezone": geo.timezone,
        "asn": geo.asn,
        "isp": geo.isp,
        "latitude": geo.latitude,
        "longitude": geo.longitude,
    }
    return {key: value for key, value in props.items() if value not in (None, "")}


def utc_timestamp(value: datetime) -> str:
    """Naive UTC datetime as ISO-8601 with an explicit Z."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
