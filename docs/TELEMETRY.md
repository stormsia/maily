# Telemetry

maily reports anonymous usage statistics about the installation to a PostHog
project. It is enabled by default, fully asynchronous, and never blocks or
fails an API request.

## What is collected

- **Installation** — a random installation id, its age, the number of process
  starts and the maily version.
- **Runtime** — Python version, OS and CPU, deployment type (docker / bare),
  database size.
- **Usage counts** — mailboxes and messages per provider (totals, unread,
  attachments), issued API keys, connected Gmail accounts, retention rules.
- **Activity per day** — mailboxes created/deleted, messages received/deleted,
  number of active clients and the most used provider domains.
- **Location** — the country of the machine's public IP address.

## What is never collected

- Email addresses — only domains and counters, never the local part.
- Message subjects, bodies, senders or recipients.
- API keys, tokens, OAuth refresh tokens or passwords.
- Gmail account addresses, hostnames, user names or file paths.
- IP addresses of the API clients.

## Where the data goes

Events are sent to the US PostHog cloud over the standard `/batch/` endpoint
with a project token built into the release. The location of the machine is
resolved once a day through `ipwho.is`. Pending events are kept in a small
local outbox and cleaned up by the regular retention sweep — 7 days for sent
events, 30 days for unsent ones.

The project token and the ingestion host are settings, not environment
variables — see `POSTHOG_PROJECT_TOKEN` and `telemetry_posthog_host` in
[src/maily/settings.py](../src/maily/settings.py). A fork that wants to send
the data somewhere else changes those two settings; while the token is still
the `POSTHOG_PLACEHOLDER_TOKEN` sentinel the telemetry module stays inactive
and never opens a network connection.

## Events

Every event carries `distinct_id` = the installation id, plus the runtime and
installation properties (`version`, `deployment`, `country_code`,
`install_age_days`, …).

| Event | When it is sent |
| --- | --- |
| `maily_install_created` | Once, the first time an installation reports. Carries the baseline usage counters. |
| `maily_app_started` | On every process start, debounced to one event per 5 minutes. |
| `maily_version_upgraded` | When the installation starts on a version different from the last one it reported. |
| `maily_setup_completed` | Once, when the installation reaches its first meaningful action. |
| `maily_first_mailbox_created` | Once, on the first mailbox. |
| `maily_first_message_received` | Once, on the first message fetched into a mailbox. |
| `maily_first_api_key_created` | Once, on the first issued API key. |
| `maily_gmail_connected` | Once, on the first connected Gmail account. |
| `maily_daily_snapshot` | Once per installation per day. Totals (`mailboxes_total`, `messages_total`, `api_keys_total`, …) plus the day's activity counters (`period_messages_received`, `period_mailboxes_created`, `period_active_owners`, …). |
| `maily_provider_daily` | Once per installation **and provider** per day, with the same counters scoped to that provider. |

The daily snapshot is built after 04:00 UTC and covers the previous day. An
installation that starts later backfills up to 7 days of history from its own
activity ledger, flagged with `is_backfill`.

## Dashboards

The PostHog project ships with three dashboards built from these events:

- **Maily — Fleet** — how many installations report, which version and
  deployment they run, where they are, and how old they are.
- **Maily — Usage** — mailboxes and messages created, deleted and received per
  day, plus the same numbers split by mail provider.
- **Maily — Activation** — the funnel from first install to first mailbox,
  first API key and first message, and how long installations keep reporting.

## Disabling telemetry

Add this line to your `.env` file (or to the environment of your container):

```bash
MAILY_TELEMETRY_ENABLED=false
```

With this flag set, the telemetry module writes nothing to the database, opens
no connections and sends no data.
