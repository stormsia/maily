"""Tests for the daily telemetry snapshot builder."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pytest

from maily.db.engine import SessionFactory, make_engine
from maily.db.models import (
    ApiKey,
    Base,
    DomainCache,
    GmailAccount,
    Mailbox,
    Message,
    Retention,
    StatsEvent,
)
from maily.providers.registry import ProviderRegistry
from maily.settings import Settings
from maily.telemetry.models import TelemetryState
from maily.telemetry.snapshot import SnapshotBuilder

DAY = date(2026, 3, 4)


class FakeClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now_utc(self) -> datetime:
        return self._now

    def today_utc(self) -> date:
        return self._now.date()


def _state() -> TelemetryState:
    return TelemetryState(
        id=1,
        installation_id="11111111-2222-4333-8444-555555555555",
        created_at=datetime(2026, 3, 1, 8, 0, 0),
        app_start_count=4,
        first_version="0.8.0",
        last_version="0.8.0",
        last_start_at=None,
        last_flush_at=None,
        last_snapshot_day=date(2026, 3, 3),
        setup_completed_at=None,
        geo_json="{}",
        geo_updated_at=None,
        last_error=None,
        updated_at=None,
    )


@pytest.mark.asyncio
async def test_snapshot_contains_totals_deltas_and_no_pii(tmp_path: Path):
    """Totals come from the live tables, deltas from the activity ledger."""
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path / 'snapshot.db'}")
    factory = SessionFactory(engine)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        async with factory() as session:
            box = Mailbox(
                provider="mailtm",
                address="alice@example.com",
                mailbox_token_enc="enc",
                is_active=True,
                is_deleted=False,
            )
            gone = Mailbox(
                provider="temp-mail.io",
                address="bob@old.test",
                mailbox_token_enc="enc",
                is_active=False,
                is_deleted=True,
            )
            session.add_all([box, gone])
            await session.flush()
            session.add(
                Message(
                    mailbox_id=box.id,
                    provider="mailtm",
                    message_api_id="m1",
                    seen=False,
                    has_attachments=True,
                    size=100,
                    is_deleted=False,
                )
            )
            session.add(
                ApiKey(
                    name="key",
                    prefix="mk_",
                    secret_enc="enc",
                    secret_sha256="a" * 64,
                    scope_json="{}",
                )
            )
            session.add(
                GmailAccount(
                    email="gmail@example.com",
                    refresh_token_enc="enc",
                    status="active",
                )
            )
            session.add(Retention(provider="mailtm", mailbox_ttl_hours=24))
            session.add(DomainCache(provider="mailtm", domains_json='["a.com","b.com"]'))
            session.add_all(
                [
                    StatsEvent(
                        day=DAY,
                        provider="mailtm",
                        domain="example.com",
                        owner_key_id=1,
                        event="mailbox_created",
                        count=2,
                    ),
                    StatsEvent(
                        day=DAY,
                        provider="mailtm",
                        domain="example.com",
                        owner_key_id=1,
                        event="message_received",
                        count=5,
                    ),
                    StatsEvent(
                        day=DAY,
                        provider="temp-mail.io",
                        domain="old.test",
                        owner_key_id=0,
                        event="mailbox_created",
                        count=1,
                    ),
                ]
            )
            await session.commit()

        settings = Settings(_env_file=None, telemetry_include_ip=False)
        builder = SnapshotBuilder(
            factory,
            ProviderRegistry(),
            settings,
            FakeClock(datetime(2026, 3, 5, 6, 0, 0)),
        )
        events = await builder.build(DAY, _state())
        by_name = {event.event_name: event for event in events}
        assert "maily_daily_snapshot" in by_name
        snapshot = by_name["maily_daily_snapshot"].properties

        assert snapshot["mailboxes_total"] == 2
        assert snapshot["mailboxes_active"] == 1
        assert snapshot["mailboxes_deleted"] == 1
        assert snapshot["messages_total"] == 1
        assert snapshot["messages_unread"] == 1
        assert snapshot["messages_with_attachments"] == 1
        assert snapshot["messages_bytes"] == 100
        assert snapshot["api_keys_total"] == 1
        assert snapshot["gmail_accounts_total"] == 1
        assert snapshot["retention_rules_total"] == 1
        assert snapshot["domain_cache_domains_total"] == 2

        assert snapshot["period_mailboxes_created"] == 3
        assert snapshot["period_messages_received"] == 5
        assert snapshot["period_active_owners"] == 1
        assert snapshot["period_distinct_domains"] == 2
        assert snapshot["period_top_domains"][0]["domain"] == "example.com"
        assert snapshot["snapshot_day"] == DAY.isoformat()
        assert snapshot["period_start"] == DAY.isoformat()
        assert snapshot["$geoip_disable"] is True
        assert snapshot["$set"]["version"]
        assert snapshot["$set_once"]["first_version"] == "0.8.0"

        provider_events = [e for e in events if e.event_name == "maily_provider_daily"]
        providers = {event.properties["provider"] for event in provider_events}
        assert providers == {"mailtm", "temp-mail.io"}
        mailtm = next(e for e in provider_events if e.properties["provider"] == "mailtm")
        assert mailtm.properties["messages_total"] == 1
        assert mailtm.properties["period_messages_received"] == 5
        assert mailtm.properties["period_mailboxes_created"] == 2
        assert mailtm.properties["period_active_owners"] == 1

        # A provider without rows of its own reports zero and never inherits
        # the fleet-wide number: temp-mail.io had no messages and no received
        # events, so it must not claim the 1 message / 5 received of the fleet.
        temp_io = next(e for e in provider_events if e.properties["provider"] == "temp-mail.io")
        assert temp_io.properties["messages_total"] == 0
        assert temp_io.properties["messages_unread"] == 0
        assert temp_io.properties["period_messages_received"] == 0
        assert temp_io.properties["period_mailboxes_created"] == 1
        assert temp_io.properties["period_active_owners"] == 0

        # The provider rows must add up to the fleet snapshot.
        assert (
            sum(e.properties["period_messages_received"] for e in provider_events)
            == snapshot["period_messages_received"]
        )
        assert (
            sum(e.properties["messages_total"] for e in provider_events)
            == snapshot["messages_total"]
        )
        assert (
            sum(e.properties["period_mailboxes_created"] for e in provider_events)
            == snapshot["period_mailboxes_created"]
        )

        # No mailbox address, subject or secret may leak into the payload.
        payload = json.dumps([event.properties for event in events], default=str)
        assert "alice" not in payload
        assert "bob" not in payload
        assert "example.com" in payload  # domains are fine, local parts are not
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_snapshot_event_uuids_are_stable(tmp_path: Path):
    """The same day always produces the same event UUIDs."""
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path / 'snapshot2.db'}")
    factory = SessionFactory(engine)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        settings = Settings(_env_file=None, telemetry_include_ip=False)
        builder = SnapshotBuilder(
            factory,
            ProviderRegistry(),
            settings,
            FakeClock(datetime(2026, 3, 5, 6, 0, 0)),
        )
        first = await builder.build(DAY, _state())
        second = await builder.build(DAY, _state())
        assert [e.event_uuid for e in first] == [e.event_uuid for e in second]
        assert all(e.occurred_at.date() == DAY for e in first)
    finally:
        await engine.dispose()
