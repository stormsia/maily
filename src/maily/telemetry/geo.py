"""Resolve the installation's public egress IP and geolocation."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .models import GeoInfo
from .ports import GeoResolver

logger = logging.getLogger("maily.telemetry.geo")


class IpWhoIsGeoResolver(GeoResolver):
    """Uses ipwho.is (or a compatible endpoint) for one IP + geo lookup per day."""

    def __init__(
        self,
        url: str = "https://ipwho.is/",
        *,
        timeout: float = 5.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._url = url
        self._timeout = timeout
        self._owns_client = client is None
        if client is None:
            client = httpx.AsyncClient(
                timeout=httpx.Timeout(timeout, connect=min(5.0, timeout)),
                follow_redirects=False,
            )
        self._client = client

    async def resolve(self, previous: Any | None = None) -> GeoInfo | None:
        try:
            response = await self._client.get(self._url)
            response.raise_for_status()
            data = response.json()
        except Exception:  # noqa: BLE001 - geo is best-effort
            logger.debug("telemetry geo lookup failed", exc_info=True)
            return None

        if not isinstance(data, dict):
            return None
        if data.get("success") is False:
            return None
        ip = data.get("ip")
        if not ip:
            return None

        raw_connection = data.get("connection")
        connection: dict[str, Any] = raw_connection if isinstance(raw_connection, dict) else {}
        asn_raw = connection.get("asn")
        try:
            asn = int(asn_raw) if asn_raw is not None else None
        except (TypeError, ValueError):
            asn = None

        def _float(key: str) -> float | None:
            raw = data.get(key)
            if raw is None:
                return None
            try:
                return float(raw)
            except (TypeError, ValueError):
                return None

        return GeoInfo(
            ip=str(ip),
            country=str(data.get("country") or ""),
            country_code=str(data.get("country_code") or ""),
            region=str(data.get("region") or ""),
            city=str(data.get("city") or ""),
            timezone=str(data.get("timezone") or ""),
            asn=asn,
            isp=str(connection.get("isp") or ""),
            latitude=_float("latitude"),
            longitude=_float("longitude"),
        )

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()
