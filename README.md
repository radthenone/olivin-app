# Olivin App

`olivin-app` to monorepo full-stack dla aplikacji sklepowej:

- `backend/` — Django + Django REST Framework,
- `frontend/` — Expo / React Native z Expo Router,
- `taskfiles/` — główne komendy developerskie przez Taskfile,
- `docs/ai/` i `.github/instructions/` — instrukcje pracy dla ludzi i agentów AI.

## Wymagania

Zainstaluj lokalnie:

- Git,
- Docker i Docker Compose,
- Taskfile (`task`),
- Python zgodny z `.python-version`,
- `uv`,
- Bun,
- Node zgodny z `.nvmrc`,
- Java 17+ oraz Android SDK, jeśli pracujesz z aplikacją na Androidzie.

Projekt zakłada komendy shellowe w składni bash. Na Windows używaj WSL albo Git Bash.

## Pierwsze uruchomienie

```bash
cp .env.example .env
task packages:backend:sync
task packages:frontend:sync
```

Uruchom backend i usługi developerskie:

```bash
task backend:build
```

Uruchom migracje:

```bash
task db:migrate
```

Uruchom frontend Expo Dev Client:

```bash
task frontend:run
```

Jeśli Metro albo routing trzyma stary stan, użyj:

```bash
task frontend:run:clear
```

## Android

Podstawowy emulator w Taskfile ma nazwę `S23`.

```bash
task emulator:run -- S23
task frontend:run -- emulator-5554
```

Budowanie i instalacja Expo Development Client:

```bash
task frontend:build:android -- emulator-5554
```

## Najważniejsze Taski

```bash
task --list
task backend:run
task backend:build
task backend:logs
task db:migrate
task db:migrations:make -- <app>
task test:backend-local -- <ścieżka>
task test:backend
task lints:backend:ruff
task lints:backend:ruff:check
task lints:backend:typecheck
task lints:frontend:lint
task lints:frontend:typecheck
task lints:frontend:format
task ovral:generate
```

Argumenty do tasków przekazuj po `--`.

## Struktura

```text
backend/
  src/
    apps/      # domeny biznesowe
    common/    # współdzielone abstrakcje
    core/      # konfiguracja, urls, celery, settings, infrastruktura
    tests/     # testy backendu

frontend/
  app/         # routing i layouty Expo Router
  src/
    api/       # klienty i typy generowane z kontraktu API
    core/      # auth, http, query, env, theme, navigation
    features/  # moduły funkcjonalne
    ui/        # współdzielone komponenty UI
```

## Kontrakt API

Nie edytuj ręcznie `frontend/src/api/generated/**`.

Po zmianach serializerów, viewsetów, URL-i albo schemy backendu:

```bash
task ovral:generate
task lints:frontend:typecheck
```

## Kontrola jakości

Dobieraj zakres kontroli do zmiany:

```bash
task test:backend-local -- <ścieżka>
task lints:backend:ruff:check
task lints:backend:typecheck
task lints:frontend:lint
task lints:frontend:typecheck
```

Pełne testy backendu w środowisku testowym:

```bash
task test:backend
```

## Instrukcje dla AI

Źródła zasad pracy:

- `AGENTS.md` — nadrzędne instrukcje repo-first,
- `docs/ai/architecture.md` — opis architektury,
- `docs/ai/workflow.md` — sposób pracy z agentami AI,
- `.github/copilot-instructions.md` i `.github/instructions/*.instructions.md` — skrócone instrukcje dla Copilota i agentów IDE.

Najważniejsza zasada: najpierw sprawdź realne pliki w repo, potem diagnozuj i proponuj zmiany.
