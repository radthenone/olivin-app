ARG UV_VERSION=0.9.4

FROM ghcr.io/astral-sh/uv:${UV_VERSION}-python3.12-bookworm-slim AS os-base

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    python3-dev \
    curl \
    git \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY backend/pyproject.toml backend/uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv lock

FROM os-base AS deps-dev
RUN uv venv /app/.venv --seed
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --extra dev --python /app/.venv/bin/python

FROM os-base AS deps-test
RUN uv venv /app/.venv --seed
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --extra test --extra dev --python /app/.venv/bin/python

FROM os-base AS runtime-base

COPY backend/src/ /app/src/

COPY docker/scripts/backend/entrypoint.sh /scripts/entrypoint.sh
COPY docker/scripts/backend/runserver.sh /scripts/runserver.sh
COPY docker/scripts/backend/check_superuser.sh /scripts/check_superuser.sh
COPY docker/scripts/backend/init-minio.sh /scripts/init-minio.sh

COPY docker/scripts/backend/celery/* /celery/
COPY docker/scripts/backend/wait_for/ /wait-for/

RUN sed -i 's/\r$//g' /celery/*.sh && chmod +x /celery/*.sh && \
    sed -i 's/\r$//g' /scripts/*.sh && chmod +x /scripts/*.sh && \
    sed -i 's/\r$//g' /wait-for/*.sh && chmod +x /wait-for/*.sh

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["/scripts/entrypoint.sh"]

FROM runtime-base AS dev
COPY --from=deps-dev /app/.venv /app/.venv

FROM runtime-base AS test
COPY --from=deps-test /app/.venv /app/.venv