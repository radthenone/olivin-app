#!/bin/sh
# Instalacja zależności przy każdym starcie kontenera: node_modules siedzą
# w nazwanym woluminie, więc po zmianie bun.lock na hoście obraz nie wie
# o nowych paczkach. Przy aktualnym lockfile bun kończy w ułamku sekundy.
set -eu

cd /app
bun install --frozen-lockfile

cd /app/web
exec bun run dev "$@"
