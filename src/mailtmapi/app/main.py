from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncEngine

from ..db.engine import SessionFactory, make_engine
from ..http import HttpClient
from ..providers.gmail.db_store import DbGmailStore
from ..providers.gmail.oauth import GmailOAuth
from ..providers.gmail.service import GmailProvider
from ..providers.mailtm import MailTM
from ..providers.registry import ProviderRegistry
from ..providers.tempmail_io import TempMailIO
from ..providers.tempmail_plus import TempMailPlus
from ..settings import Settings, get_settings
from .services.retention import retention_worker, run_sweep
from .errors import register_errors
from .routers.admin import router as admin_router
from .routers.gmail import public as gmail_public
from .routers.gmail import router as gmail_router
from .routers.health import router as health_router
from .routers.mailboxes import router as mailboxes_router
from .routers.messages import router as messages_router
from .routers.providers import router as providers_router


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
    engine: AsyncEngine = make_engine(settings.database_url)
    _run_migrations(settings.database_url)
    factory = SessionFactory(engine)
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
        [gmail, MailTM(http=http), TempMailPlus(http=http), TempMailIO(http=http)]
    )
    app.state.engine = engine
    app.state.session_factory = factory
    app.state.registry = registry
    app.state.http = http
    app.state.gmail = gmail
    app.state.oauth = oauth
    app.state.oauth_states = {}

    sweep_task = asyncio.create_task(
        retention_worker(
            lambda: run_sweep(factory, registry, settings),
            settings.retention_interval_seconds,
        )
    )
    try:
        yield
    finally:
        sweep_task.cancel()
        try:
            await sweep_task
        except asyncio.CancelledError:
            pass
        await registry.close()
        await http.close()
        await engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="mailtmapi", lifespan=lifespan)
    app.state.settings = settings
    register_errors(app)
    app.include_router(health_router)
    app.include_router(gmail_public)
    app.include_router(providers_router)
    app.include_router(gmail_router)
    app.include_router(mailboxes_router)
    app.include_router(messages_router)
    app.include_router(admin_router)
    static_dir = Path(__file__).resolve().parents[1] / "static"
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