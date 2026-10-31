from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine

from .. import __version__
from ..db.engine import SessionFactory, make_engine
from ..http import HttpClient
from ..providers.anonymmail_net import AnonymMailNet
from ..providers.dispoemail_org import DispoEmailOrg
from ..providers.gmail.db_store import DbGmailStore
from ..providers.gmail.oauth import GmailOAuth
from ..providers.gmail.service import GmailProvider
from ..providers.mailtm import MailTM
from ..providers.noopmail_org import NoopMail
from ..providers.registry import ProviderRegistry
from ..providers.temp_tf import TempTF
from ..providers.tempmail_io import TempMailIO
from ..providers.tempmail_plus import TempMailPlus
from ..settings import Settings, get_settings
from .errors import register_errors
from .middleware.origin import OriginGuard
from .routers.admin import router as admin_router
from .routers.gmail import public as gmail_public
from .routers.gmail import router as gmail_router
from .routers.health import router as health_router
from .routers.keys import me_router as keys_me_router
from .routers.keys import router as keys_router
from .routers.mailboxes import router as mailboxes_router
from .routers.messages import router as messages_router
from .routers.providers import router as providers_router
from .services import domain_cache as dc
from .services import provider_headers as ph
from .services import stats_history
from .services.retention import retention_worker, run_sweep

OPENAPI_TAGS = [
    {
        "name": "System",
        "description": "Liveness, readiness and client-facing configuration.",
    },
    {
        "name": "Providers",
        "description": "Enabled temp-mail providers and their usable posting targets.",
    },
    {
        "name": "Mailboxes",
        "description": "Create, list, look up and delete disposable mailboxes.",
    },
    {
        "name": "Messages",
        "description": "Read, mark, delete and download messages for a mailbox.",
    },
    {
        "name": "Gmail",
        "description": "Import Gmail accounts, OAuth pairing and per-account sync.",
    },
    {
        "name": "Admin",
        "description": "Operational controls: retention TTLs, domain cache and Gmail credentials.",
    },
    {
        "name": "Keys",
        "description": "Issued API keys are root-only except GET /me.",
    },
]


_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def _refuse_open_bind(settings: Settings) -> None:
    host = settings.host.strip().lower()
    if settings.api_key or host in _LOOPBACK_HOSTS:
        return
    raise RuntimeError(
        "Refusing to listen on a non-loopback address without an API key. "
        "Set MAILTM_API_KEY or bind MAILTM_HOST to 127.0.0.1."
    )


def _run_migrations(url: str) -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config()
    root = Path(__file__).resolve().parents[3]
    cfg.set_main_option("script_location", str(root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url.replace("sqlite+aiosqlite", "sqlite"))
    command.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    _refuse_open_bind(settings)
    # Resolve (and pin) the Fernet key before any request can race to mint one.
    settings.resolved_secret_key()
    engine: AsyncEngine = make_engine(settings.database_url)
    _run_migrations(settings.database_url)
    factory = SessionFactory(engine)
    # Seed the ledger's receive-counters from messages that predate the ledger,
    # so the 7-day incoming chart doesn't fall back to live rows and then
    # silently lose past days to retention deletes. Idempotent per day.
    async with factory() as session:
        seeded = await stats_history.backfill_received(session)
        await session.commit()
        if seeded:
            logger.info(
                "stats: seeded message_received for {} day/provider bucket(s)",
                seeded,
            )
    http = HttpClient(proxy=settings.proxy)
    secret = settings.resolved_secret_key()
    store = DbGmailStore(factory, secret)
    try:
        cid, csec = settings.gmail_client()
    except RuntimeError:
        cid, csec = "", ""
    oauth = GmailOAuth(
        cid,
        csec,
        http,
        token_uri=settings.gmail_token_uri,
        auth_uri=settings.gmail_auth_uri,
    )
    if not cid:
        from .services import gmail_config as gcfg

        async with factory() as session:
            db_creds = await gcfg.get_creds(session, secret)
        if db_creds:
            oauth.configure(*db_creds)
    gmail = GmailProvider(store, oauth, http)
    registry = ProviderRegistry(
        [
            gmail,
            MailTM(http=http),
            TempMailPlus(http=http),
            TempMailIO(http=http),
            NoopMail(http=http),
            AnonymMailNet(http=http),
            DispoEmailOrg(http=http),
            TempTF(
                http=http,
                gmail_dot=settings.temp_tf_gmail_dot,
                gmail_plus=settings.temp_tf_gmail_plus,
            ),
        ]
    )
    await ph.bootstrap(factory, http, registry, settings)
    app.state.engine = engine
    app.state.session_factory = factory
    app.state.registry = registry
    app.state.http = http
    app.state.gmail = gmail
    app.state.oauth = oauth
    app.state.oauth_states = {}
    sweep_lock = asyncio.Lock()
    app.state.sweep_lock = sweep_lock

    sweep_task = asyncio.create_task(
        retention_worker(
            lambda: run_sweep(factory, registry, settings, lock=sweep_lock),
            settings.retention_interval_seconds,
        )
    )
    cache_task = asyncio.create_task(
        dc.domain_cache_worker(factory, registry, settings)
    )
    headers_task = asyncio.create_task(
        ph.provider_headers_worker(factory, http, registry, settings)
    )
    try:
        yield
    finally:
        for task in (sweep_task, cache_task, headers_task):
            task.cancel()
        with suppress(asyncio.CancelledError):
            await sweep_task
        with suppress(asyncio.CancelledError):
            await cache_task
        with suppress(asyncio.CancelledError):
            await headers_task
        await registry.close()
        await http.close()
        await engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(
        title="mailtmapi",
        version=__version__,
        lifespan=lifespan,
        description=(
            "Local multi-provider temporary-email API. "
            "Most endpoints require the `X-API-Key` header (see Admin → API key in the dashboard)."
        ),
        openapi_tags=OPENAPI_TAGS,
        docs_url=None,
        redoc_url=None,
        swagger_ui_parameters={
            "docExpansion": "none",
            "filter": True,
            "displayRequestDuration": True,
            "persistAuthorization": True,
        },
    )
    app.state.settings = settings
    register_errors(app)
    app.include_router(health_router)
    app.include_router(gmail_public)
    app.include_router(providers_router)
    app.include_router(gmail_router)
    app.include_router(mailboxes_router)
    app.include_router(messages_router)
    app.include_router(admin_router)
    app.include_router(keys_me_router)
    app.include_router(keys_router)
    app.add_middleware(OriginGuard)
    static_dir = Path(__file__).resolve().parents[1] / "static"

    @app.get("/docs", include_in_schema=False)
    async def docs(_: Request) -> FileResponse:
        return FileResponse(static_dir / "docs.html")

    if static_dir.is_dir():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    return app


def run() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "mailtmapi.app.main:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
    )


if __name__ == "__main__":
    run()
