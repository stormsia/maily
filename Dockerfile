# syntax=docker/dockerfile:1.7
# ==============================================================================
# Ultra-Lean Production Multi-Stage Dockerfile for mailtmapi
# ==============================================================================

# ---------- Stage 1: Build & Dependencies ----------
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/venv

WORKDIR /app

# 1. Dependencies: cached via BuildKit cache mount (/root/.cache/uv).
# Code changes will not invalidate downloaded wheels or the dependency layer.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# 2. Source code: copy components needed for package build and migrations
COPY README.md pyproject.toml alembic.ini ./
COPY src/ ./src/
COPY alembic/ ./alembic/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ---------- Stage 2: Minimal Runtime ----------
FROM python:3.14-slim-bookworm AS runner

WORKDIR /app

# Python and glibc memory allocator optimizations (minimal RAM fragmentation for asyncio + SQLite WAL)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONMALLOC=malloc \
    MALLOC_ARENA_MAX=2 \
    PATH="/venv/bin:$PATH" \
    VIRTUAL_ENV=/venv \
    PYTHONPATH=/app/src \
    MAILTM_HOST=0.0.0.0 \
    MAILTM_PORT=8477 \
    MAILTM_DATABASE_URL="sqlite+aiosqlite:////data/mailtm.db" \
    MAILTM_SECRET_KEY_PATH="/data/mailtm.key"

# 1. Create unprivileged mailtm user and /data working directory
RUN groupadd -g 1000 mailtm && \
    useradd -u 1000 -g mailtm -d /app -s /sbin/nologin mailtm && \
    mkdir -p /data /app && \
    chown -R mailtm:mailtm /data /app

# 2. Copy compiled venv, code, and Alembic configuration
COPY --from=builder --chown=mailtm:mailtm /venv /venv
COPY --from=builder --chown=mailtm:mailtm /app/src /app/src
COPY --from=builder --chown=mailtm:mailtm /app/alembic /app/alembic
COPY --from=builder --chown=mailtm:mailtm /app/alembic.ini /app/alembic.ini

# 3. Entrypoint to auto-fix permissions on mounted /data volume (SQLite WAL) and drop privileges to mailtm
RUN printf '#!/bin/sh\n\
set -e\n\
if [ "$(id -u)" = "0" ]; then\n\
    if [ -d "/data" ]; then\n\
        chown -R mailtm:mailtm /data 2>/dev/null || true\n\
        chmod -R 775 /data 2>/dev/null || true\n\
        chmod -R 666 /data/*.db* /data/*.key* 2>/dev/null || true\n\
    fi\n\
    exec runuser -u mailtm -g mailtm -- "$@"\n\
else\n\
    exec "$@"\n\
fi\n' > /entrypoint.sh && chmod +x /entrypoint.sh

VOLUME ["/data"]
EXPOSE 8477

# Reliable Healthcheck (HTTP 200 check on dynamic port, exec form without shell process)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import os, sys, urllib.request; port = os.getenv('MAILTM_PORT', '8477'); sys.exit(0 if urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=3).status == 200 else 1)"]

ENTRYPOINT ["/entrypoint.sh"]
CMD ["mailtmapi"]
