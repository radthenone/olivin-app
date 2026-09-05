# Overlay olivin-app — tylko unikalne informacje tego repo

## Kontekst

Monorepo full-stack: `frontend/` (Expo Router 6, SDK 54) + `backend/` (Django 5.2 + DRF).
**Stan implementacji:** auth + accounts są żywe; shop/payments w większości szkielet — referencja w `_temp/ecommerce_*_blueprint/`.

## Wersje i narzędzia (lockfile = prawda)

| Warstwa | Wersja / narzędzie |
|---------|-------------------|
| Python | 3.12.10 (`.python-version`) |
| Backend PM | **uv** — `uv sync --extra dev` |
| Django / DRF | 5.2.11 / 3.16.1 (`uv.lock`) |
| Typecheck BE | **Pyrefly** (`task lints:backend:typecheck`) — **nie MyPy** (CI krok myli nazwę) |
| Lint BE | Ruff 0.15.0 |
| Node | 20.19.2 (`.nvmrc`) |
| Frontend PM | **Bun** — `bun install --frozen-lockfile` |
| Expo / RN / React | SDK 54 / 0.81.5 / 19.1 |
| Testy BE | pytest 9, markery `unit` / `integration` / `slow` |

## Taskfile — obowiązkowy punkt wejścia

Główny plik: `Taskfile.yml` (import z `taskfiles/`). Namespace to **`packages:`**, nie `app:frontend:*` (opisy w `packages.yml` mogą być nieaktualne).

| Namespace | Plik | Przykłady |
|-----------|------|-----------|
| `backend` | `taskfiles/backend.yml` | `task backend:run`, `task backend:build` |
| `db` | `taskfiles/db.yml` | `task db:migrate`, `task db:migrations:make -- accounts` |
| `test` | `taskfiles/test.yml` | `task test:backend-local -- src/tests/accounts/` |
| `frontend` | `taskfiles/frontend.yml` | `task frontend:run` (Dev Client), `task frontend:run:go` |
| `ovral` | `taskfiles/ovral.yml` | `task ovral:generate` |
| `lints` | `taskfiles/lints.yml` | `task lints:backend:ruff:check`, `task lints:frontend:typecheck` |
| `translation` | `taskfiles/translation.yml` | `task translation:run`, `task translation:generate` |
| `precommit` | `taskfiles/precommit.yml` | `task precommit:install`, `task precommit:run` |

Argumenty tasków: po `--`, np. `task db:migrations:make -- accounts`.

## Shell

Komendy w **bash** (Git Bash na Windows). Nie PowerShell.

## Porty i env

| Zmienna / usługa | Wartość dev |
|------------------|-------------|
| `DJANGO_PORT` | **8020** |
| Postgres host | **5434** (`olivin-postgres`) |
| `EXPO_PUBLIC_BACKEND_URL` | `127.0.0.1:8020` (web / iOS) |
| `EXPO_PUBLIC_EMULATOR_URL` | `10.0.2.2:8020` (Android emulator) |
| `EXPO_PUBLIC_VERSION` | `v1` — wersjonowanie API (`URLPathVersioning`) |
| Sieć Docker | **`olivin-network`** (musi istnieć przed `docker compose up`) |

## Docker Compose (dev)

Plik: `docker-compose.yml`.

| Kontener | Rola | Profil |
|----------|------|--------|
| `olivin-postgres` | PostgreSQL 16 | dev/backend |
| `olivin-redis` | Cache + Celery broker | dev/test |
| `olivin-minio` | S3-compatible | dev/test |
| `olivin-mailhog` | SMTP dev | dev |
| `olivin-django` | Django / DRF | dev |
| `olivin-celery-worker/beat/flower` | Celery | profile `celery` |
| `olivin-libretranslate` | Tłumaczenia maszynowe | profile `translation` |

Exec: `docker exec -it olivin-django <komenda>` lub task, np. `task db:migrate`.
Testy integracyjne: `docker-compose.test.yml`, cov fail-under **60%**.

## Web vs mobile (Expo)

| Cel | Komenda / uwagi |
|-----|-----------------|
| **Mobile (domyślnie)** | `task frontend:run` — Dev Client + Metro `--lan --dev-client` + Android |
| Expo Go (bez native) | `task frontend:run:go` |
| Metro sam | `task frontend:metro` |
| Android build Dev Client | `task frontend:build:android` |
| **Web** | Brak dedykowanego taska — `cd frontend && bunx expo start --web` |
| OAuth / social login | Wymaga **Dev Client** (nie Expo Go) |

Platforma w kodzie: `moduleSuffixes: [".native", ".web", ""]` w `tsconfig.json`.
Pliki: `session-token.storage.native.ts` (SecureStore) vs `.web.ts` (cookies).
Allauth client: **`app`** (mobile) vs **`browser`** (web) — `src/core/auth/platform.ts`.

## Auth (allauth headless — nie JWT)

- Backend: django-allauth headless (`browser` / `app`), MFA, social (Google, Facebook).
- API sesji: `_allauth/{browser|app}/v1/...` — **osobny** klient Orval (`auth-mutator.ts`).
- Mobile: nagłówek **`X-Session-Token`** + `expo-secure-store`.
- Web: cookies `sessionid` + CSRF, `credentials: include`.
- Profile/adresy DRF: prefix **`customers/`** (np. `customers/profile`, `customers/addresses`) — nie zakładaj `/api/v1/profiles/` w URL path.
- Frontend: `src/core/auth/`, `src/features/auth/`, ekrany `authorize.tsx`, `oauthredirect.tsx`.

## Orval — dual schema

Nie edytuj `frontend/src/api/generated/**`.

| Wejście | URL | Mutator |
|---------|-----|---------|
| Allauth | `/_allauth/openapi.json` | `auth-mutator.ts` |
| DRF apps | `/api/schema/` | domyślny |

`APPS_TAGS` w `frontend/orval.config.js` (obecnie): **`Addresses`, `Profiles`, `Health`** — rozszerzaj przy dodawaniu viewsetów domenowych.

Sekwencja po zmianie API:

1. Backend + `schema.yaml` / spectacular
2. `task ovral:generate`
3. `task lints:frontend:typecheck`

## Storage (stan faktyczny)

- **Brak** `apps/files/` — storage w `backend/src/core/storage/` (MinIO dev, S3 prod przez `USE_AWS`).
- Buckety: static, media, profiles, products, private-media.
- `Product.image` = **`ImageField`** (obecna deviacja względem docelowego `file_id` z capability files).
- Migracja do `apps/files` + `StoredFile` — planowana, nie zaimplementowana.

## Payments (stan faktyczny)

- `stripe` w `pyproject.toml`, **`apps/payments` pusty** (szkielet).
- **Brak** `@stripe/stripe-react-native` w `frontend/package.json`.
- Wzorzec implementacji: `backend/src/_temp/ecommerce_backend_blueprint/`, `frontend/_temp/ecommerce_frontend_blueprint/`.
- Bundle MCP `payments` opisuje **docelowy** flow — nie implementuj Stripe w produkcyjnym `src/` bez jawnego zadania.

## Shop / domena (stan faktyczny)

| App | Stan |
|-----|------|
| `accounts` | żywy — User, Profile, Address, testy |
| `products` | częściowy — Product, Variant, `TranslatableModel`, `ImageField` |
| `orders`, `payments`, … | szkielet (admin, puste views/models) |
| Frontend `features/catalog\|cart\|checkout` | **brak** w produkcyjnym `src/` |

Tłumaczenia katalogu: `common.TranslatableModel`, JSON `translations`, LibreTranslate (`task translation:*`).

## Integracje — ścieżka docelowa

Kod adapterów: **`core/integrations/`** (mail, allauth, storage…).
Settings/Celery mogą jeszcze wskazywać legacy **`core.services.*`** — przy nowym kodzie używaj `core/integrations/`; migracja ścieżek w settings w toku.

## Struktura katalogów

**Frontend:** `app/`, `src/core/`, `src/features/`, `src/api/generated/`, `src/ui/`.

**Backend:** `core/`, `apps/`, `common/`, `schema.yaml`, `tests/` (pytest, nie per-app `tests.py`).

Blueprint referencyjny: `backend/src/_temp/ecommerce_backend_blueprint/`, `frontend/_temp/ecommerce_frontend_blueprint/`.

## CI (`.github/workflows/ci.yml`)

**Backend:** uv sync → ruff → **Pyrefly** → `task test:backend-local -- src/ -m "not integration"`.

**Frontend:** bun frozen → eslint → tsc → prettier.

**Czego CI nie robi (jeszcze):** job `api-contract` (Orval diff), `task test:backend` w Dockerze, testy frontendowe, EAS build.

## Pre-commit

Lokalnie: `task precommit:install` — ruff, eslint, prettier (`.pre-commit-config.yaml`).
**Nie uruchamiane w CI** — PR polega na jobach GitHub Actions.

## Kontrole po zmianach

- Backend: `task test:backend-local -- <ścieżka>`, `task lints:backend:ruff:check`, `task lints:backend:typecheck`
- Frontend: `task lints:frontend:lint:check`, `task lints:frontend:typecheck`
