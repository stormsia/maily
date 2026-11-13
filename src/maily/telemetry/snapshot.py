"""Build the daily PostHog snapshot from database aggregates."""

from __future__ import annotations

import json
import uuid
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from typing import Any

from sqlalchemy import and_, case, func, or_, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker

from .. import __version__
from ..app.services.stats_history import (
    EVENT_MAILBOX_CREATED,
    EVENT_MAILBOX_DELETED,
    EVENT_MESSAGE_DELETED,
    EVENT_MESSAGE_RECEIVED,
)
from ..db.models import (
    ApiKey,
    DomainCache,
    GmailAccount,
    Mailbox,
    Message,
    Retention,
    StatsEvent,
)
from ..db.models import (
    TelemetryEvent as TelemetryEventRow,
)
from ..providers.registry import ProviderRegistry
from ..settings import Settings
from .models import GeoInfo, OutboxCounts, TelemetryEvent, TelemetryState
from .ports import Clock
from .privacy import (
    deployment,
    geo_properties,
    installation_properties,
    runtime_properties,
    sanitize_properties,
)

_DELTA_KEYS = {
    EVENT_MAILBOX_CREATED: "period_mailboxes_created",
    EVENT_MAILBOX_DELETED: "period_mailboxes_deleted",
    EVENT_MESSAGE_RECEIVED: "period_messages_received",
    EVENT_MESSAGE_DELETED: "period_messages_deleted",
}

#: Counters that describe a single provider. A provider row must carry its own
#: numbers, never the fleet-wide ones.
_PROVIDER_SCOPED_KEYS = (
    "mailboxes_total",
    "mailboxes_active",
    "mailboxes_deleted",
    "messages_total",
    "messages_deleted",
    "messages_active",
    "messages_unread",
    "messages_with_attachments",
    "messages_bytes",
    "period_mailboxes_created",
    "period_mailboxes_deleted",
    "period_messages_received",
    "period_messages_deleted",
    "period_active_owners",
)

#: Counters that describe the installation as a whole. They are identical on
#: every provider row and are carried over unchanged.
_INSTALLATION_COUNTER_KEYS = (
    "api_keys_total",
    "api_keys_active",
    "api_keys_expired",
    "gmail_accounts_total",
    "gmail_accounts_active",
    "retention_rules_total",
    "domain_cache_providers",
    "domain_cache_domains_total",
)


class SnapshotBuilder:
    def __init__(
        self,
        factory: async_sessionmaker[Any],
        registry: ProviderRegistry | None,
        settings: Settings,
        clock: Clock,
    ) -> None:
        self._factory = factory
        self._registry = registry
        self._settings = settings
        self._clock = clock

    async def build(
        self,
        day: date,
        state: TelemetryState,
        *,
        is_backfill: bool = False,
    ) -> list[TelemetryEvent]:
        today = self._clock.today_utc()
        now = self._clock.now_utc()

        async with self._factory() as session:
            global_totals, provider_totals = await self._collect_totals(session, now)
            global_deltas, provider_deltas = await self._collect_deltas(session, day)
            db_size = await self._db_size(session)
            dialect = self._dialect(session)
            outbox = await self._outbox_counts(session)

        registered = list(self._registry.slugs()) if self._registry is not None else []
        providers = sorted(set(registered) | set(provider_totals) | set(provider_deltas))

        # Metadata that describes the installation, shared by the fleet snapshot
        # and every provider row.
        shared: dict[str, Any] = runtime_properties(self._settings, __version__)
        shared.update(installation_properties(state, today))
        shared.update(
            {
                "db_dialect": dialect,
                "db_size_bytes": db_size,
                "provider_count": len(providers),
                "providers": ",".join(providers),
                "telemetry_pending": outbox.pending_events,
                "telemetry_failed": outbox.failed_events,
            }
        )

        geo = GeoInfo.from_json(state.geo_json) if state.geo_json else None
        shared.update(geo_properties(geo, include_ip=self._settings.telemetry_include_ip))

        base: dict[str, Any] = {**shared, **global_totals, **global_deltas}

        if self._settings.telemetry_person_profiles:
            base["$set"] = {
                "version": __version__,
                "country_code": geo.country_code if geo else "",
                "deployment": deployment(),
                "mailboxes_total": global_totals.get("mailboxes_total", 0),
                "messages_total": global_totals.get("messages_total", 0),
                "provider_count": len(providers),
            }
            base["$set_once"] = {
                "installation_created_at": (
                    state.created_at.isoformat() if state.created_at else ""
                ),
                "first_version": state.first_version,
            }

        period_start = day.isoformat()
        period_end = (day + timedelta(days=1)).isoformat()
        occurred_at = datetime.combine(day, time(23, 59, 59))
        namespace = uuid.NAMESPACE_URL

        global_event = TelemetryEvent(
            event_uuid=str(
                uuid.uuid5(
                    namespace,
                    f"{state.installation_id}:maily_daily_snapshot:{day.isoformat()}",
                )
            ),
            event_name="maily_daily_snapshot",
            distinct_id=state.installation_id,
            properties=sanitize_properties(
                {
                    **base,
                    "period_start": period_start,
                    "period_end": period_end,
                    "snapshot_day": day.isoformat(),
                    "is_backfill": is_backfill,
                }
            ),
            occurred_at=occurred_at,
        )
        events = [global_event]

        for provider in providers:
            provider_props = dict(shared)
            for key in _INSTALLATION_COUNTER_KEYS:
                if key in global_totals:
                    provider_props[key] = global_totals[key]
            # Counters that belong to a single provider must not inherit the
            # fleet-wide number: a provider without rows in a bucket reports
            # zero, otherwise an idle provider would look like the busiest one
            # in the fleet.
            for key in _PROVIDER_SCOPED_KEYS:
                provider_props[key] = 0
            provider_props.update(provider_totals.get(provider, {}))
            provider_props.update(provider_deltas.get(provider, {}))
            for key in _PROVIDER_SCOPED_KEYS:
                provider_props.setdefault(key, 0)
            provider_props.update(
                {
                    "provider": provider,
                    "period_start": period_start,
                    "period_end": period_end,
                    "snapshot_day": day.isoformat(),
                    "is_backfill": is_backfill,
                }
            )
            events.append(
                TelemetryEvent(
                    event_uuid=str(
                        uuid.uuid5(
                            namespace,
                            f"{state.installation_id}:maily_provider_daily:{day.isoformat()}:{provider}",
                        )
                    ),
                    event_name="maily_provider_daily",
                    distinct_id=state.installation_id,
                    properties=sanitize_properties(provider_props),
                    occurred_at=occurred_at,
                )
            )
        return events

    async def _collect_totals(
        self, session: Any, now: datetime
    ) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
        mailbox_rows = (
            await session.execute(
                select(
                    Mailbox.provider,
                    func.count(),
                    func.sum(case((Mailbox.is_active.is_(True), 1), else_=0)),
                    func.sum(case((Mailbox.is_deleted.is_(True), 1), else_=0)),
                ).group_by(Mailbox.provider)
            )
        ).all()
        message_rows = (
            await session.execute(
                select(
                    Message.provider,
                    func.count(),
                    func.sum(case((Message.is_deleted.is_(True), 1), else_=0)),
                    func.sum(
                        case(
                            (
                                and_(
                                    Message.is_deleted.is_(False),
                                    Message.seen.is_(False),
                                ),
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    func.sum(
                        case(
                            (
                                and_(
                                    Message.is_deleted.is_(False),
                                    Message.has_attachments.is_(True),
                                ),
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    func.coalesce(
                        func.sum(
                            case(
                                (Message.is_deleted.is_(False), Message.size),
                                else_=0,
                            )
                        ),
                        0,
                    ),
                ).group_by(Message.provider)
            )
        ).all()

        by_provider: dict[str, dict[str, Any]] = {}
        for provider, total, active, deleted in mailbox_rows:
            by_provider.setdefault(provider, {}).update(
                {
                    "mailboxes_total": int(total or 0),
                    "mailboxes_active": int(active or 0),
                    "mailboxes_deleted": int(deleted or 0),
                }
            )
        for provider, total, deleted, unread, attachments, size in message_rows:
            by_provider.setdefault(provider, {}).update(
                {
                    "messages_total": int(total or 0),
                    "messages_deleted": int(deleted or 0),
                    "messages_active": int(total or 0) - int(deleted or 0),
                    "messages_unread": int(unread or 0),
                    "messages_with_attachments": int(attachments or 0),
                    "messages_bytes": int(size or 0),
                }
            )

        global_props: dict[str, Any] = {
            "mailboxes_total": sum(
                int(row.get("mailboxes_total", 0)) for row in by_provider.values()
            ),
            "mailboxes_active": sum(
                int(row.get("mailboxes_active", 0)) for row in by_provider.values()
            ),
            "mailboxes_deleted": sum(
                int(row.get("mailboxes_deleted", 0)) for row in by_provider.values()
            ),
            "messages_total": sum(
                int(row.get("messages_total", 0)) for row in by_provider.values()
            ),
            "messages_deleted": sum(
                int(row.get("messages_deleted", 0)) for row in by_provider.values()
            ),
            "messages_active": sum(
                int(row.get("messages_active", 0)) for row in by_provider.values()
            ),
            "messages_unread": sum(
                int(row.get("messages_unread", 0)) for row in by_provider.values()
            ),
            "messages_with_attachments": sum(
                int(row.get("messages_with_attachments", 0)) for row in by_provider.values()
            ),
            "messages_bytes": sum(
                int(row.get("messages_bytes", 0)) for row in by_provider.values()
            ),
        }

        key_total = int((await session.scalar(select(func.count()).select_from(ApiKey))) or 0)
        key_active = int(
            (
                await session.scalar(
                    select(func.count())
                    .select_from(ApiKey)
                    .where(or_(ApiKey.expires_at.is_(None), ApiKey.expires_at > now))
                )
            )
            or 0
        )
        gmail_total = int(
            (await session.scalar(select(func.count()).select_from(GmailAccount))) or 0
        )
        gmail_active = int(
            (
                await session.scalar(
                    select(func.count())
                    .select_from(GmailAccount)
                    .where(GmailAccount.status == "active")
                )
            )
            or 0
        )
        retention_rules = int(
            (await session.scalar(select(func.count()).select_from(Retention))) or 0
        )
        cache_rows = (await session.execute(select(DomainCache.domains_json))).all()
        cache_domains = 0
        for row in cache_rows:
            raw = row[0] if row else ""
            try:
                parsed = json.loads(raw)
            except (ValueError, TypeError):
                parsed = []
            if isinstance(parsed, list):
                cache_domains += len(parsed)

        global_props.update(
            {
                "api_keys_total": key_total,
                "api_keys_active": key_active,
                "api_keys_expired": key_total - key_active,
                "gmail_accounts_total": gmail_total,
                "gmail_accounts_active": gmail_active,
                "retention_rules_total": retention_rules,
                "domain_cache_providers": len(cache_rows),
                "domain_cache_domains_total": cache_domains,
            }
        )
        return global_props, by_provider

    async def _collect_deltas(
        self, session: Any, day: date
    ) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
        rows = (
            await session.execute(
                select(
                    StatsEvent.provider,
                    StatsEvent.event,
                    func.sum(StatsEvent.count),
                )
                .where(StatsEvent.day == day)
                .group_by(StatsEvent.provider, StatsEvent.event)
            )
        ).all()
        global_counts: dict[str, int] = {}
        provider_counts: dict[str, dict[str, int]] = defaultdict(dict)
        for provider, event, count in rows:
            key = _DELTA_KEYS.get(event)
            if key is None:
                continue
            value = int(count or 0)
            global_counts[key] = global_counts.get(key, 0) + value
            provider_counts[provider][key] = provider_counts[provider].get(key, 0) + value

        owner_rows = (
            await session.execute(
                select(
                    StatsEvent.provider,
                    func.count(func.distinct(StatsEvent.owner_key_id)),
                )
                .where(
                    StatsEvent.day == day,
                    StatsEvent.owner_key_id != 0,
                )
                .group_by(StatsEvent.provider)
            )
        ).all()
        for provider, owners in owner_rows:
            value = int(owners or 0)
            provider_counts[provider]["period_active_owners"] = value

        global_owners = int(
            (
                await session.scalar(
                    select(func.count(func.distinct(StatsEvent.owner_key_id))).where(
                        StatsEvent.day == day,
                        StatsEvent.owner_key_id != 0,
                    )
                )
            )
            or 0
        )

        distinct_domains = int(
            (
                await session.scalar(
                    select(func.count(func.distinct(StatsEvent.domain))).where(
                        StatsEvent.day == day,
                        StatsEvent.domain != "",
                    )
                )
            )
            or 0
        )
        top_domains = [
            {"domain": domain, "count": int(count or 0)}
            for domain, count in (
                (
                    await session.execute(
                        select(StatsEvent.domain, func.sum(StatsEvent.count))
                        .where(StatsEvent.day == day, StatsEvent.domain != "")
                        .group_by(StatsEvent.domain)
                        .order_by(func.sum(StatsEvent.count).desc())
                        .limit(10)
                    )
                ).all()
            )
        ]

        global_props = {
            "period_active_owners": global_owners,
            "period_distinct_domains": distinct_domains,
            "period_top_domains": top_domains,
        }
        global_props.update(global_counts)
        provider_props = {provider: dict(values) for provider, values in provider_counts.items()}
        return global_props, provider_props

    async def _outbox_counts(self, session: Any) -> OutboxCounts:
        pending = int(
            (
                await session.scalar(
                    select(func.count())
                    .select_from(TelemetryEventRow)
                    .where(TelemetryEventRow.status == "pending")
                )
            )
            or 0
        )
        failed = int(
            (
                await session.scalar(
                    select(func.count())
                    .select_from(TelemetryEventRow)
                    .where(TelemetryEventRow.status == "failed")
                )
            )
            or 0
        )
        return OutboxCounts(pending_events=pending, failed_events=failed)

    async def _db_size(self, session: Any) -> int | None:
        bind = session.get_bind()
        if bind is None:
            return None
        if bind.dialect.name == "sqlite":
            page_count = (await session.execute(text("PRAGMA page_count"))).scalar()
            page_size = (await session.execute(text("PRAGMA page_size"))).scalar()
            return int(page_count or 0) * int(page_size or 0)
        if bind.dialect.name == "postgresql":
            size = (
                await session.execute(text("SELECT pg_database_size(current_database())"))
            ).scalar()
            return int(size) if size is not None else None
        return None

    @staticmethod
    def _dialect(session: Any) -> str:
        bind = session.get_bind()
        return bind.dialect.name if bind is not None else "unknown"
