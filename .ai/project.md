# Overlay olivin-app — wyłącznie stan faktyczny tego repo

**Zasada tego pliku:** opisuje to, co JEST, nigdy to, co ma być. Plany mieszkają w zgłoszeniach na trackerze, decyzje w `docs/adr/`, słownik domeny w `CONTEXT.md`. Jeśli ten plik rozjedzie się z kodem, kod ma rację — zgłoś rozjazd zamiast budować na opisie.

Zweryfikowano: 2026-09-09.

## Gdzie czego szukać

| Czego szukasz | Gdzie |
| --- | --- |
| Znaczenie pojęcia domenowego | `CONTEXT.md` |
| Dlaczego zdecydowano tak, a nie inaczej | `docs/adr/` |
| Co ma powstać | zgłoszenia na trackerze |
| Wzorzec implementacji sklepu (referencja, nie prawda) | `backend/src/_temp/`, `frontend/_temp/` |

## Stan implementacji — mierzony, nie deklarowany

**Żywe:**

- `backend/src/apps/accounts` — User, Profile, Address, managery, serializery, serwisy, widoki, schematy. Testy w `backend/src/tests/accounts/`.
- `backend/src/core/` — settings (django-split-settings), integracje, storage, utils (w tym health check w `core/utils/health/`).
- `backend/src/common/` — pola, modele bazowe w tym `TranslatableModel`, lokalizacja.
- `frontend/` — aplikacja Expo: ekrany auth (logowanie, rejestracja, MFA, weryfikacja e-mail, reset hasła, logowanie kodem), konto, profil. Klienty Orval.

**Puste szkielety po `startapp` — dziewięć linii kodu każdy, zero modeli, zero migracji:**

`products`, `categories`, `orders`, `payments`, `discounts`, `inventory`, `shipping`, `reviews`, `notifications`, `analytics`

Nie zakładaj, że którakolwiek z nich cokolwiek zawiera. Nie ma modelu Product, nie ma Order, nie ma Cart.

**Nie istnieje po stronie frontendu:** `features/catalog`, `features/cart`, `features/checkout`, `features/orders`, `features/payments`. Są tylko `auth`, `account`, `profile`.

**Znany defekt:** `apps/products` ma jednocześnie `models.py` i pusty katalog `models/` (oraz `selectors/`, `serializers/`, `views/`). Pakiet przesłania moduł. Katalogi są puste, więc git ich nie śledzi.

## Wersje i narzędzia (lockfile = prawda)

| Warstwa | Wersja / narzędzie |
| --- | --- |
| Python | 3.12.10 (`.python-version`) |
| Backend PM | **uv** — `uv sync --extra dev` |
| Django / DRF | 5.2.11 / 3.16.1 (`uv.lock`) |
| Typecheck BE | **Pyrefly** — `task lints:backend:typecheck`. Nie MyPy. |
| Lint BE | Ruff |
| Node | 20.19.2 (`.nvmrc`) |
| Frontend PM | **Bun** — `bun install --frozen-lockfile` |
| Expo / RN / React | SDK 54 / 0.81.5 / 19.1 |
| Styling mobile | NativeWind 4.2 (Tailwind v3) |
| Stan | TanStack Query (serwer) + Zustand (klient) |
| Formularze | react-hook-form + Zod |
| Testy BE | pytest 9, markery `unit` / `integration` / `slow` |
| Testy FE | **brak** — żadnego runnera w `package.json` |

## Taskfile — obowiązkowy punkt wejścia

Główny plik `Taskfile.yml`, importy z `taskfiles/`. Istniejące namespace'y: `backend`, `db`, `frontend`, `emulator`, `shell`, `packages`, `ovral`, `test`, `lints`, `precommit`.

Argumenty tasków po `--`, np. `task db:migrations:make -- accounts`.

Przykłady: `task backend:run`, `task db:migrate`, `task test:backend-local -- src/tests/accounts/`, `task frontend:run` (Dev Client), `task ovral:generate`, `task lints:frontend:typecheck`.

**Brak taska na uruchomienie weba** — dziś `cd frontend && bunx expo start --web`.

## Shell

Komendy w **bash** (Git Bash na Windowsie). Nie PowerShell.

## Porty i env

| Zmienna / usługa | Wartość dev |
| --- | --- |
| `DJANGO_PORT` | **8020** |
| Postgres host | **5434** (`olivin-postgres`) |
| `EXPO_PUBLIC_BACKEND_URL` | `127.0.0.1:8020` (web / iOS) |
| `EXPO_PUBLIC_EMULATOR_URL` | `10.0.2.2:8020` (emulator Androida) |
| `EXPO_PUBLIC_VERSION` | `v1` — wersjonowanie API (`URLPathVersioning`) |
| Sieć Docker | **`olivin-network`** — musi istnieć przed `docker compose up` |

Zmienne ładowane z `.env` oraz `.envs/dev/**` przez `dotenv:` w `Taskfile.yml`.

## Docker Compose (dev)

`docker-compose.yml` definiuje **osiem** usług:

`olivin-postgres` (PostgreSQL 16), `olivin-redis` (cache + broker), `olivin-minio` (S3-compatible), `olivin-mailhog` (SMTP dev), `olivin-django`, `olivin-celery-worker`, `olivin-celery-beat`, `olivin-celery-flower`.

Profile: `dev`, `backend`, `full`, `local`, `test`.

Exec: `docker exec -it olivin-django <komenda>` albo task.
Testy integracyjne: `docker-compose.test.yml`, próg pokrycia **60%**.

## Auth (allauth headless — nie JWT)

- Backend: django-allauth headless (klienty `browser` / `app`), MFA, social (Google, Facebook). **GitHub nie jest skonfigurowany.**
- API sesji: `_allauth/{browser|app}/v1/...` — **osobny** klient Orval (`auth-mutator.ts`).
- Mobile: nagłówek **`X-Session-Token`** + `expo-secure-store`.
- Web: cookies `sessionid` + CSRF, `credentials: include`.
- Profile i adresy przez DRF pod prefiksem **`customers/`** (`customers/profile`, `customers/addresses`) — nie zakładaj `/api/v1/profiles/`.
- Frontend: `src/core/auth/`, `src/features/auth/`, ekrany `authorize.tsx`, `oauthredirect.tsx`.
- `djangorestframework-simplejwt` jest w zależnościach, ale **nie jest używany** — pozostałość.

## Orval — dual schema

**Nie edytuj `frontend/src/api/generated/**` ręcznie.**

| Wejście | URL | Mutator |
| --- | --- | --- |
| Allauth | `/_allauth/openapi.json` | `auth-mutator.ts` |
| DRF apps | `/api/schema/` | `app-mutator.ts` |

Generowane są też schematy Zod (`.zod.ts`) dla obu wejść.

`APPS_TAGS` w `frontend/orval.config.js` (obecnie): **`Addresses`, `Profiles`, `Health`**. Nowy viewset domenowy bez dopisania tagu nie trafi do klienta — cichy błąd.

Sekwencja po zmianie API: backend → migracje → regeneracja `schema.yaml` → tag w `APPS_TAGS` → `task ovral:generate` → `task lints:frontend:typecheck`.

## Web vs mobile (Expo, stan obecny)

| Cel | Komenda |
| --- | --- |
| Mobile (domyślnie) | `task frontend:run` — Dev Client + Metro `--lan --dev-client` + Android |
| Expo Go (bez modułów natywnych) | `task frontend:run:go` |
| Metro sam | `task frontend:metro` |
| Build Dev Client | `task frontend:build:android` |
| Web | brak taska — `cd frontend && bunx expo start --web` |

`web.output: "static"` w `app.config.js`. Platforma w kodzie przez `moduleSuffixes: [".native", ".web", ""]`. Pliki: `session-token.storage.native.ts` (SecureStore) vs `.web.ts` (cookies). Wybór klienta allauth: `src/core/auth/platform.ts`.

OAuth wymaga **Dev Client**, nie działa w Expo Go.

## Storage

- **Brak `apps/files`.** Storage w `backend/src/core/storage/` — MinIO w dev, S3 w prod przez `USE_AWS`.
- Buckety: static, media, profiles, products, private-media.

## Payments

- `stripe` w `pyproject.toml`, `apps/payments` **pusty**.
- **Brak** jakiejkolwiek zależności Stripe w `frontend/package.json`.
- Nie implementuj Stripe bez jawnego zadania.

## Integracje

Adaptery w **`core/integrations/`** (mail, allauth). Settings i Celery mogą jeszcze wskazywać legacy `core.services.*` — nowy kod pisz pod `core/integrations/`.

## Struktura katalogów (stan obecny)

**Frontend:** `app/` (routing Expo Router), `src/core/`, `src/features/`, `src/api/generated/`, `src/ui/` (`primitives/`, `layout/`, `feedback/`, `platform/`).

**Backend:** `core/`, `apps/`, `common/`, `schema.yaml`, `tests/` (centralnie, nie per-app `tests.py`).

**Tokeny designu:** `frontend/tailwind.config.js` ma zdefiniowane wyłącznie breakpointy. `theme.extend` jest **pusty** — brak palety, typografii i skali odstępów.

## CI (`.github/workflows/ci.yml`)

**Backend:** uv sync → Ruff → Pyrefly → `task db:migrations:check` → `task backend:schema:check` → `task test:backend-local -- src/ -m "not integration"`.

**Frontend:** bun frozen → ESLint → tsc → Prettier.

**Pre-commit:** osobny job uruchamiający te same hooki co `git commit`.

**Czego CI nie robi:** bramki diffu Orvala (schemat jest pilnowany, wygenerowany klient nie), testów integracyjnych w Dockerze, żadnych testów frontendu, buildów EAS ani buildu weba.

## Kontrole po zmianach

- Backend: `task test:backend-local -- <ścieżka>`, `task lints:backend:ruff:check`, `task lints:backend:typecheck`
- Frontend: `task lints:frontend:lint:check`, `task lints:frontend:typecheck`

## Planowana przebudowa — jeszcze NIE wykonana

Zaplanowane jest przeniesienie `frontend/` do monorepo Turborepo z osobną aplikacją Next.js (`frontend/web/`), przeniesioną aplikacją Expo (`frontend/mobile/`) i pakietami współdzielonymi (`frontend/packages/`). **Nic z tego jeszcze nie istnieje.** Do czasu wykonania obowiązuje struktura opisana wyżej.
