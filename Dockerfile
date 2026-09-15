# mailtmapi — минимизированный multi-stage образ
#
# Stage 1 (build): собирает venv; весь мусор сборки (pip cache, метаданные
#   hatchling, build-зависимости) остаётся в этом слое и не попадает в образ.
# Stage 2 (runtime): только python-slim + готовый venv + исходники (editable,
#   т.к. миграции alembic ищут ./alembic относительно src).

# ---------- BUILD ----------
FROM python:3.14-slim AS build

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore

WORKDIR /app
COPY . .

# editable: магия hatchling, код живёт в /app/src, alembic рядом — миграции работают
RUN python -m venv /venv && /venv/bin/pip install --no-cache-dir -e .

# ---------- RUNTIME ----------
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/venv/bin:$PATH" \
    VIRTUAL_ENV=/venv \
    MAILTM_HOST=0.0.0.0 \
    MAILTM_PORT=8477 \
    MAILTM_DATABASE_URL="sqlite+aiosqlite:////data/mailtm.db" \
    MAILTM_SECRET_KEY_PATH="/data/mailtm.key"

# только то, что нужно в рантайме: код, миграции, venv
COPY --from=build /venv /venv
COPY --from=build /app/src /app/src
COPY --from=build /app/alembic /app/alembic
COPY --from=build /app/alembic.ini /app/alembic.ini

# non-root: pid 1 не root, данные только в /data
RUN useradd -m -u 1000 -d /home/mailtm mailtm \
    && mkdir -p /data && chown -R mailtm:mailtm /data /home/mailtm

USER mailtm
WORKDIR /app

VOLUME ["/data"]
EXPOSE 8477

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8477/health', timeout=3)"

CMD ["mailtmapi"]