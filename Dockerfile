# mailtmapi — минимизированный multi-stage образ на uv
#
# Stage 1 (build): uv sync по uv.lock (`--frozen` = образ собирается ровно из
#   лок-файла, без пересборки разрешений). Установка только prod-зависимостей
#   (`--no-dev`); корневой пакет ставится editable (дефолт uv sync) — как и
#   раньше с `pip install -e .`, чтобы alembic видел ./alembic от src.
#   Первый sync без проекта кешируется по паре pyproject.toml+uv.lock и
#   переиспользуется между сборками; uv-кэш wheels живёт в своём слое.
# Stage 2 (runtime): python-slim + готовый venv + исходники; uv в рантайме
#   не нужен.

# ---------- BUILD ----------
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS build

# без скачивания uv-менеджерных python: в образе уже системный 3.14;
# без байткода в venv (PYTHONDONTWRITEBYTECODE закроет добор на рантайме)
# UV_PROJECT_ENVIRONMENT: venv сразу в /venv — uv пишет абсолютные пути
# (шебанг `#!/venv/bin/python3`) в консольные скрипты, и COPY без переноса
# пути их не ломает
ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/venv

WORKDIR /app

# сначала только метаданные + lockfile: смена кода не отменяет слои зависимостей
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# код проекта + editable-установка корневого пакета
COPY . .
RUN uv sync --frozen --no-dev

# ---------- RUNTIME ----------
# та же база (bookworm, glibc), что в build-стадии: venv-шебанг ведёт на
# /usr/local/bin/python3.14, а собранные wheels летают без пересборки
FROM python:3.14-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/venv/bin:$PATH" \
    VIRTUAL_ENV=/venv \
    MAILTM_HOST=0.0.0.0 \
    MAILTM_PORT=8477 \
    MAILTM_DATABASE_URL="sqlite+aiosqlite:////data/mailtm.db" \
    MAILTM_SECRET_KEY_PATH="/data/mailtm.key"

# только то, что нужно в рантайме: код, миграции, venv (путь совпадает с билдом)
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