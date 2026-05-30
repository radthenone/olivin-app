ARG UV_VERSION=0.9.4
ARG PYTHON_VERSION=3.12

FROM ghcr.io/astral-sh/uv:${UV_VERSION}-python${PYTHON_VERSION}-bookworm-slim AS build-base

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    gcc \
    python3-dev \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY backend/pyproject.toml backend/uv.lock ./

FROM build-base AS deps-prod
RUN uv venv /app/.venv --seed
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev --python /app/.venv/bin/python

FROM build-base AS deps-dev
RUN uv venv /app/.venv --seed
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --extra dev --python /app/.venv/bin/python

FROM build-base AS deps-test
RUN uv venv /app/.venv --seed
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --extra dev --extra test --python /app/.venv/bin/python

FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime-base

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    && install -d /usr/share/postgresql-common/pgdg \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | \
    gpg --dearmor -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.gpg \
    && echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.gpg] http://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update && apt-get install -y --no-install-recommends \
    redis-tools \
    postgresql-client-16 \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/src/ /app/src/

COPY docker/scripts/backend/entrypoint.sh /scripts/entrypoint.sh
COPY docker/scripts/backend/runserver.sh /scripts/runserver.sh
COPY docker/scripts/backend/backup.sh /scripts/backup.sh
COPY docker/scripts/backend/check_superuser.sh /scripts/check_superuser.sh
COPY docker/scripts/backend/init-minio.sh /scripts/init-minio.sh

COPY docker/scripts/backend/celery/* /celery/
COPY docker/scripts/backend/wait_for/ /wait-for/

RUN sed -i 's/\r$//g' /celery/*.sh /scripts/*.sh /wait-for/*.sh \
    && chmod +x /celery/*.sh /scripts/*.sh /wait-for/*.sh

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["/scripts/entrypoint.sh"]

FROM runtime-base AS dev
COPY --from=deps-dev /app/.venv /app/.venv

FROM runtime-base AS test
COPY --from=deps-test /app/.venv /app/.venv

FROM runtime-base AS prod
COPY --from=deps-prod /app/.venv /app/.venv
