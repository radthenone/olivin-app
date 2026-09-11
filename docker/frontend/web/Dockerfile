# Obraz deweloperski aplikacji webowej. Kod źródłowy monorepo frontendu jest
# montowany jako wolumin w czasie działania, a node_modules żyją w nazwanych
# woluminach — obraz zawiera tylko runtime Bun i skrypt startowy.
#
# Bundler aplikacji mobilnej celowo nie jest tu obecny:
# docs/adr/0007-bundler-mobilny-poza-kontenerem.md
ARG BUN_VERSION=1.3.13

FROM oven/bun:${BUN_VERSION}-slim AS dev

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

COPY docker/frontend/web/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 3000

ENTRYPOINT ["/entrypoint.sh"]
