ARG UV_VERSION=0.9.4

FROM ghcr.io/astral-sh/uv:${UV_VERSION}-python3.12-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    python3-dev \
    curl \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_SYSTEM_PYTHON=1

COPY backend/pyproject.toml backend/uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --all-extras

COPY backend/src/ /app/src/

COPY docker/scripts/backend/entrypoint.sh /scripts/entrypoint.sh
COPY docker/scripts/backend/runserver.sh /scripts/runserver.sh
COPY docker/scripts/backend/check_superuser.sh /scripts/check_superuser.sh
COPY docker/scripts/backend/init-minio.sh /scripts/init-minio.sh

COPY docker/scripts/backend/celery/* /celery/
COPY docker/scripts/backend/wait_for/ /wait-for/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --all-extras

# Make all scripts executable
RUN sed -i 's/\r$//g' /celery/*.sh && chmod +x /celery/*.sh && \
    sed -i 's/\r$//g' /scripts/*.sh && chmod +x /scripts/*.sh && \
    sed -i 's/\r$//g' /wait-for/*.sh && chmod +x /wait-for/*.sh

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["/scripts/entrypoint.sh"]