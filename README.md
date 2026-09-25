# mailtmapi

**Self-hosted temporary email API with a beautiful admin dashboard.**

Create disposable mailboxes on demand, receive mail in real time, and read
confirmation links or codes — all through one clean REST API, an async Python
client, and a dark themed web UI. Runs locally or in Docker, stores everything
in SQLite, and protects your data with optional API-key auth and encrypted
credentials.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite)
![License](https://img.shields.io/badge/license-MIT-blue)

---

## ✨ Features

- **Multi-provider mailboxes** — `mail.tm`, `tempmail.plus`, and Gmail
  (`+alias` addresses on your own Google account via OAuth)
- **Inbox & reading** — list messages, read subject/body/HTML, view raw source,
  mark as read, delete
- **Confirmation email extraction** — wait for an email and pull out the
  confirmation link or digit code automatically
- **SQLite storage** — no external database required; messages are cached locally
- **Retention policy** — automatic TTL-based cleanup of old mailboxes and messages
- **Admin dashboard** — dark-themed SPA with stats, charts, and per-page management
- **Async Python client** — typed, documented, `async with`-friendly
- **Responsive & polished** — works from desktop to phone
- **Docker-ready** — minimal multi-stage image, one-command deploy

---

## 🚀 Quick start

### Option A — Docker (recommended)

```bash
git clone https://github.com/stormsia/mailtmapi.git && cd mailtmapi
cp .env.example .env        # adjust if needed
docker compose up -d --build
```

Open <http://127.0.0.1:8477/> — the admin dashboard is ready.

### Option B — Local (Python 3.10+)

```bash
git clone https://github.com/stormsia/mailtmapi.git && cd mailtmapi
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -e ".[dev]"
mailtmapi                       # starts on 127.0.0.1:8477
```

The server reads `.env` if present (see [Configuration](#-configuration)); with
no `.env` it runs with defaults: SQLite in the current directory, no API key.
Migrations run automatically on startup — no manual setup.

Development server (with auto-reload on code changes):

```bash
uvicorn mailtmapi.app.main:create_app --factory --reload --port 8477
```

---

## 🖥️ Web dashboard

The admin UI is served at `http://127.0.0.1:8477/` and includes:

| Page | What you can do |
|---|---|
| **Overview** | Stats cards, provider split chart, 7-day mail trend, retention status, one-click sweep |
| **Mailboxes** | Search, filter by provider, create, open, delete |
| **Mailbox detail** | Paged message list, reading pane, formatted/raw HTML, source viewer, mark read, delete |
| **Retention** | Per-provider TTL rules (mailboxes / messages) and manual sweep |
| **Gmail** | OAuth connect, manage connected accounts, sync, delete |

If `MAILTM_API_KEY` is set, the dashboard asks for it once and stores it in
your browser's localStorage.

---

## 🔐 Configuration

Copy `.env.example` to `.env` and adjust. Full reference:

| Variable | Default | Description |
|---|---|---|
| `MAILTM_HOST` | `127.0.0.1` | Bind address (`0.0.0.0` inside Docker) |
| `MAILTM_PORT` | `8477` | HTTP port |
| `MAILTM_API_KEY` | *(empty)* | Root key. Issued keys live in the database. Empty on loopback is open root; if set, requests need `X-API-Key` |
| `MAILTM_DATABASE_URL` | `sqlite+aiosqlite:///mailtm.db` | SQLite location; use `////data/mailtm.db` in Docker |
| `MAILTM_SECRET_KEY` | *(auto)* | Fernet key for encrypting stored credentials; auto-generated into `mailtm.key` if empty |
| `MAILTM_PROXY` | *(empty)* | Outbound proxy for provider requests |
| `MAILTM_RETENTION_INTERVAL_SECONDS` | `60` | How often the retention sweep runs |
| `MAILTM_GMAIL_CLIENT_ID` | *(empty)* | Google OAuth client ID |
| `MAILTM_GMAIL_CLIENT_SECRET` | *(empty)* | Google OAuth client secret |

> **Gmail OAuth**: set the env vars above *or* open the dashboard → **Gmail** →
> **Set up OAuth** and paste your Client ID / Secret / Redirect URI. The secret
> is stored encrypted with your `MAILTM_SECRET_KEY`. Redirect URI defaults to
> `http://{host}:{port}/v1/gmail/oauth/callback`.
>
> To allow *any* Google account to sign in, publish your OAuth consent screen
> (testing mode only permits accounts you whitelist).

---

## 📡 REST API

All endpoints are under `/v1`. Send `X-API-Key` with the root key (`MAILTM_API_KEY`) or an issued key. If `MAILTM_API_KEY` is empty and the server is on loopback, the API is open as root. Errors return `{"detail": "..."}`.

> **Auth-free:** `GET /health` and `GET /v1/config` (server facts used by the
> dashboard and the standalone client's auto-update) never need the key.

An unknown or expired key is `401` `{"detail": "invalid api key"}` with the header `X-MailTM-Error: api_key`. A known key that lacks an action, or that touches another owner's row, is `403` `{"detail": "forbidden"}` without that header.

Key scope: an empty `providers` list grants all providers. An empty `parent_ids` list grants no Gmail parents. Gmail mailbox addresses must be plus-aliases.

### Providers & targets

| Method | Path | Description |
|---|---|---|
| `GET` | `/v1/providers` | List providers (`kind`: `domain` / `parent`) |
| `GET` | `/v1/targets?provider=` | Domains or Gmail accounts usable for creation |

### Mailboxes

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/mailboxes` | Create mailbox (`provider`, `domain`/`parent_id`, optional `address`, `password`) |
| `GET` | `/v1/mailboxes?provider=&active=` | List the caller's mailboxes |
| `GET` | `/v1/mailboxes/by-address/{email}` | Find by full address |
| `GET` | `/v1/mailboxes/{id}` | Get one of the caller's mailboxes |
| `DELETE` | `/v1/mailboxes/{id}` | Delete mailbox (provider + local) |

List and get are scoped to the caller. Another owner's mailbox is `403`, not `404`. A missing row is `404`.

### Messages

| Method | Path | Description |
|---|---|---|
| `GET` | `/v1/mailboxes/{id}/messages?page=` | List messages (fetches from provider, caches locally) |
| `GET` | `/v1/mailboxes/{id}/messages/{msg_id}` | Full message with `text` + `html` |
| `POST` | `/v1/mailboxes/{id}/messages/{msg_id}/read` | Mark as read |
| `DELETE` | `/v1/mailboxes/{id}/messages/{msg_id}` | Delete message |
| `GET` | `/v1/mailboxes/{id}/messages/{msg_id}/source` | Raw source |

### Gmail

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/gmail/oauth/start` | Get OAuth URL + state |
| `GET` | `/v1/gmail/accounts` | Connected accounts |
| `POST` | `/v1/gmail/accounts/import` | Import existing `refresh_token` / `token_json` |
| `POST` | `/v1/gmail/accounts/{id}/sync` | Refresh profile & send-as aliases |
| `DELETE` | `/v1/gmail/accounts/{id}` | Disconnect account |

### Admin

| Method | Path | Description |
|---|---|---|
| `GET` | `/v1/admin/stats` | Mailbox/message stats, provider split, 7-day trend |
| `GET` | `/v1/admin/retention` | Current TTL rules |
| `PUT` | `/v1/admin/retention/{provider}` | Set TTLs (`mailbox_ttl_hours`, `message_ttl_hours`) |
| `DELETE` | `/v1/admin/retention/{provider}` | Disable rules for a provider |
| `POST` | `/v1/admin/retention/run` | Run cleanup sweep now |
| `GET/PUT/DELETE` | `/v1/admin/gmail/creds` | Manage stored OAuth credentials |

### Keys

Every keys route is root-only except `GET /v1/admin/keys/me`, which any authenticated key may call. Root's `/me` body is `{"is_root": true}`. The secret comes back only from create, rotate, and `GET /{id}/secret`.

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/admin/keys` | Create a key. The response includes the secret once |
| `GET` | `/v1/admin/keys` | List keys. Secrets are omitted |
| `GET` | `/v1/admin/keys/me` | Current principal. Any authenticated key. Root returns `{"is_root": true}` |
| `GET` | `/v1/admin/keys/{id}` | One key, without the secret |
| `GET` | `/v1/admin/keys/{id}/secret` | Reveal the stored secret |
| `PATCH` | `/v1/admin/keys/{id}` | Update name, expiry, and scope. The secret is unchanged |
| `PUT` | `/v1/admin/keys/{id}/retention` | Replace that key's retention rows |
| `POST` | `/v1/admin/keys/{id}/rotate` | Rotate the secret. The new secret is returned once |
| `DELETE` | `/v1/admin/keys/{id}` | Delete the key. `409` if it still owns a live mailbox or gmail account |

Interactive API docs: <http://127.0.0.1:8477/docs> (Swagger UI).

---

## 🐍 Python client

Two ways to use the client:

### Standalone (recommended, pip + auto-update)

`client/client.py` is a **self-contained single file** — it pulls only
`httpx`, `loguru` and `pydantic`, not the server stack (FastAPI, SQLAlchemy,
uvicorn, …). Works standalone or installed from this git repo:

```bash
# install from git (any project/venv):
pip install "mailtmapi-client @ git+https://github.com/stormsia/mailtmapi.git#subdirectory=client"

# …or just copy the file into your project:
curl -O https://raw.githubusercontent.com/stormsia/mailtmapi/main/client/client.py
```

```python
from client import MailTMAPI  # if installed/copied standalone

async with MailTMAPI("http://127.0.0.1:8477", api_key="sk-...") as api:
    mb = await api.mailboxes.create(provider="mail.tm")
    res = await api.messages.wait_for_confirmation_email(
        mb.id,
        sender_domain="gmail.com",
        url_contain=["confirm", "verify"],
        digit_code_mask=r"(\d{6})",
        timeout=120,
    )
    await api.mailboxes.delete(mb.id)
```

**Auto-update from git.** The client carries its own `__version__` and knows
where to fetch its canonical source (`MAILTMAPI_CLIENT_SOURCE`, defaults to
`main` branch of this repo). Check or apply updates with:

```bash
mailtmapi-client check     # "update available: 0.2.0 -> 0.3.0" (exit 2) or up-to-date
mailtmapi-client update    # downloads newer client.py and replaces the installed file
mailtmapi-client version
```

`update` is a plain file write — restart your scripts afterwards for the new
version to apply. Inside your code:

```python
from client import check_update, self_update

up = check_update()          # ("0.2.0", "0.3.0") or None
self_update()                # True if the file was replaced
```

The server also advertises its release version at `GET /v1/config`
(`client_version`, no API key needed). `api.check_client_version()` compares it
to the local `__version__` and logs a warning with the update command when the
server is newer. To keep the version matrix honest, a CI/suite test
(`tests/test_client_standalone.py`) pins the client version to the server's.

### Bundled with the app (`mailtmapi` package)

The same client is shipped inside the server package (used by the dashboard,
tests and `sdk.py`):

```python
from mailtmapi.client import MailTMAPI

async def main():
    async with MailTMAPI("http://127.0.0.1:8477", api_key="sk-...") as api:
        mb = await api.mailboxes.create(provider="mail.tm")
        print("mailbox:", mb.address)

asyncio.run(main())
```

### Client structure

```
MailTMAPI                        # public entry point (async with / close)
├── .health      HealthAPI       GET /health
├── .config      ConfigAPI       GET /v1/config (api_key_required, client_version)
├── .providers   ProvidersAPI    providers + targets
├── .mailboxes   MailboxesAPI    create / list / get / by_address / delete
├── .messages    MessagesAPI     list / get / mark_read / delete / source
│                               wait_for / wait_for_confirmation_email
├── .gmail       GmailAPI        OAuth start / import / accounts / sync
└── .admin       AdminAPI        stats / retention / domain cache / gmail creds / keys
```

### Issued keys (`0.3.0`)

`AdminAPI` (`api.admin`) key methods, client version `0.3.0`:

- `keys` lists keys. The secret is not in the response.
- `key_create` creates a key and returns the secret once.
- `key_get` returns one key without the secret.
- `key_me` works for any authenticated key. Root gets `{"is_root": true}`.
- `key_secret` reveals the stored secret.
- `key_update` changes name, expiry, and scope. The secret stays the same.
- `key_retention_set` replaces that key's retention rows.
- `key_rotate` issues a new secret and returns it once.
- `key_delete` deletes the key. `409` if it still owns a live mailbox or gmail account.

### Waiting helpers

```python
# any new message, then mark it read
msg = await api.messages.wait_for(mb.id, timeout=60, mark_seen=True)

# confirmation email with optional sender filter, link keywords, code regex
res = await api.messages.wait_for_confirmation_email(
    mb.id,
    sender_domain="gmail.com",
    url_contain=["confirm"],
    digit_code_mask=r"(\d{6})",
)
```

---

## 🗑️ Retention

Retention lets you automatically delete old mailboxes and messages per provider:

- `mailbox_ttl_hours` — mailboxes older than the TTL are removed (provider-side deletes are best-effort)
- `message_ttl_hours` — messages older than the TTL are removed
- The sweep runs every `MAILTM_RETENTION_INTERVAL_SECONDS`, or manually via
  `POST /v1/admin/retention/run` / the dashboard button

---

## 🧪 Development

```bash
pip install -e ".[dev]"
pytest            # run the test suite
ruff check src tests
mypy src
```

CI (`.github/workflows/ci.yml`) runs exactly the same commands plus a
`node --check` syntax pass for the static JS (there is no build step /
`package.json`).

The test suite is hermetic: **every** `Settings(...)` in `tests/` passes
`_env_file=None`, so a local `.env` (`MAILTM_API_KEY`, proxy, …) can never
leak into test runs and cause spurious 401s / network calls. Keep it that way
in new tests. Shared provider stubs live in `tests/helpers.py` — don't copy
`StubProvider` into new test files.

Project layout:

```
src/mailtmapi/
├── app/            # FastAPI app: routers, services, schemas, deps
├── db/             # SQLAlchemy models & engine
├── providers/      # provider adapters: mail.tm, tempmail.plus, gmail
├── static/         # admin dashboard (plain HTML/JS/CSS — no build step)
├── client.py       # async Python client (Pydantic + loguru + httpx)
├── sdk.py          # deprecated alias imports (warns)
├── settings.py     # pydantic-settings configuration
├── http.py         # shared HTTP client with proxy support
├── crypto.py       # Fernet encryption for stored credentials
└── exceptions.py   # error types
client/             # standalone pip-installable client (client.py + pyproject.toml)
alembic/            # migrations (auto-applied on startup)
tests/              # pytest suite
```

---

## 🐳 Docker

Minimal multi-stage image — the build stage installs dependencies into a clean
venv, and the runtime stage copies only what's needed (no build cache, no junk).

```bash
docker compose up -d --build
```

- Data (SQLite + encryption key) lives in the `mailtmapi_data` volume at `/data`
- Runs as a **non-root** user with `no-new-privileges` and `init: true`
- Healthcheck pings `/health` automatically

### Updating & recreating the stack (bulletproof)

The plain `docker compose up -d --build` rebuilds the image only when a layer
changes and leaves an existing container in place, so a stale image or a
half-updated container can survive. To force a **full, deterministic
recreate** of the stack — without touching your data:

```bash
docker compose down --remove-orphans              # stop & remove containers (data volume stays)
docker compose build --pull --no-cache            # rebuild image from scratch (fresh base images, no cache)
docker compose up -d --force-recreate             # start brand-new containers from the new image
```

One-liner:

```bash
docker compose down --remove-orphans && docker compose build --pull --no-cache && docker compose up -d --force-recreate
```

- `--pull` / `--no-cache` make the rebuild deterministic — every layer is
  rebuilt on the latest base image, so no stale layer can leak into the update.
- `--remove-orphans` and `--force-recreate` guarantee the old containers are
  gone and brand-new ones run the fresh image.
- Your mailboxes, messages and settings are **safe**: they live in the
  `mailtmapi_data` named volume, which these commands never delete.
- If you ever want to wipe *everything* including data, add `-v` to the first
  command (`docker compose down -v`) — there is no way back.

---

## 📄 License

MIT