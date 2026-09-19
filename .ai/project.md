# Overlay olivin-app — wyłącznie stan faktyczny tego repo

**Zasada tego pliku:** opisuje to, co JEST, nigdy to, co ma być. Plany mieszkają w zgłoszeniach na trackerze, decyzje w `docs/adr/`, słownik domeny w `CONTEXT.md`. Jeśli ten plik rozjedzie się z kodem, kod ma rację — zgłoś rozjazd zamiast budować na opisie.

Zweryfikowano: 2026-09-11.

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
- `backend/src/core/` — settings (django-split-settings), integracje, storage, utils. Health check: **`GET /health/`** (nie pod `/api/`), zwraca stan bazy, Redisa i storage.
- `backend/src/common/` — pola, modele bazowe w tym `TranslatableModel`, lokalizacja.
- `frontend/mobile/` — aplikacja Expo: ekrany auth (logowanie, rejestracja, MFA, weryfikacja e-mail, reset hasła, logowanie kodem), konto, profil.
- `frontend/web/` — aplikacja Next.js 16 (App Router, Tailwind v4). **Jedna trasa**: strona główna ze stanem zdrowia backendu. Zero ekranów sklepu.
- `frontend/packages/` — `@olivin/config` (tsconfig, eslint, prettier, loader env), `@olivin/tokens` (tokeny designu, CommonJS + d.ts), `@olivin/api` (klient Orval obu schematów + kontrakt transportu), `@olivin/schemas` i `@olivin/money` (**puste** szkielety).

**Puste szkielety po `startapp` — dziewięć linii kodu każdy, zero modeli, zero migracji:**

`products`, `categories`, `orders`, `payments`, `discounts`, `inventory`, `shipping`, `reviews`, `notifications`

Nie zakładaj, że którakolwiek z nich cokolwiek zawiera. Nie ma modelu Product, nie ma Order, nie ma Cart.

**Nie istnieje po stronie frontendu:** `features/catalog`, `features/cart`, `features/checkout`, `features/orders`, `features/payments`. Są tylko `auth`, `account`, `profile`.

**Znany defekt:** `apps/products` ma jednocześnie `models.py` i pusty katalog `models/` (oraz `selectors/`, `serializers/`, `views/`). Pakiet przesłania moduł. Katalogi są puste, więc git ich nie śledzi.

## Wersje i narzędzia (lockfile = prawda)

| Warstwa | Wersja / narzędzie |
| --- | --- |
| Python | 3.12.10 (`.python-version`) |
| Backend PM | **uv** — `uv sync --extra dev` |
| Django / DRF | **6.0.8** / 3.18.1 (`uv.lock`) — Django podbity o wersję główną w #51 |
| Typecheck BE | **Pyrefly** — `task lints:backend:typecheck`. Nie MyPy. |
| Lint BE | Ruff |
| Node | 22.23.2 (`.nvmrc`) — React Native 0.86 wymaga ^20.19.4 albo ^22.13 |
| Frontend PM | **Bun** — `bun install --frozen-lockfile` |
| Expo / RN / React | SDK 57 / 0.86.3 / 19.2 |
| Web | Next.js 16 (Turbopack), Tailwind v4, React 19.2 (przypięty do wersji z Expo) |
| Monorepo JS | Bun workspaces (`linker = "hoisted"`) + Turborepo 2 |
| Styling mobile | NativeWind 4.2 (Tailwind v3) |
| Stan | TanStack Query (serwer) + Zustand (klient) |
| Formularze | react-hook-form + Zod |
| Testy BE | pytest 9, markery `unit` / `integration` / `slow` |
| Testy FE | **brak** — żadnego runnera w `package.json` |

## Taskfile — obowiązkowy punkt wejścia

Główny plik `Taskfile.yml`, importy z `taskfiles/`. Istniejące namespace'y: `backend`, `db`, `mobile`, `web`, `emulator`, `shell`, `packages`, `ovral`, `test`, `lints`, `precommit`.

Argumenty tasków po `--`, np. `task db:migrations:make -- accounts`.

Przykłady: `task backend:run`, `task db:migrate`, `task test:backend-local -- src/tests/accounts/`, `task mobile:run` (Dev Client), `task ovral:generate`, `task lints:frontend:typecheck`.

Namespace `mobile:` obsługuje aplikację Expo. Namespace `lints:frontend:*` obejmuje **wszystkie** workspace'y JavaScriptu i idzie przez Turborepo.

Web: `task web:run` (dev, port 3000), `task web:build`, `task web:tokens` (regeneracja `app/tokens.css` z pakietu tokenów).

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

**Nie edytuj `frontend/packages/api/generated/**` ręcznie.**

| Wejście | Plik (nie HTTP) | Mutator |
| --- | --- | --- |
| Allauth | `backend/src/allauth-schema.json` (snapshot; odśwież `task ovral:schema:allauth`) | `src/auth-mutator.ts` |
| DRF apps | `backend/src/schema.yaml` (pilnowany przez `backend:schema:check`) | `src/app-mutator.ts` |

Generowane są też schematy Zod (`.zod.ts`) dla obu wejść.

`APPS_TAGS` w `frontend/packages/api/orval.config.js` (obecnie): **`Addresses`, `Profiles`, `Health`**. Nowy viewset domenowy bez dopisania tagu nie trafi do klienta — cichy błąd.

Sekwencja po zmianie API: backend → migracje → regeneracja `schema.yaml` → tag w `APPS_TAGS` → `task ovral:generate` → `task lints:frontend:typecheck`. Bramka: `task ovral:check` (offline, w CI).

## Web vs mobile (Expo, stan obecny)

| Cel | Komenda |
| --- | --- |
| Mobile (domyślnie) | `task mobile:run` — Dev Client + Metro `--lan --dev-client` + Android |
| Expo Go (bez modułów natywnych) | `task mobile:run:go` |
| Metro sam | `task mobile:metro` |
| Build Dev Client | `task mobile:build:android` |
| Regeneracja projektu natywnego | `task mobile:prebuild:clean` |
| Web | `task web:run` — Next dev na porcie 3000, natywnie, poza Dockerem |

`web.output: "static"` w `app.config.js`. Platforma w kodzie przez `moduleSuffixes: [".native", ".web", ""]`. Pliki: `session-token.storage.native.ts` (SecureStore) vs `.web.ts` (cookies). Wybór klienta allauth: `src/core/auth/platform.ts`.

OAuth wymaga **Dev Client**, nie działa w Expo Go.

## Storage

- **Brak `apps/files`.** Storage w `backend/src/core/storage/` — MinIO w dev, S3 w prod przez `USE_AWS`.
- Buckety dziś w kodzie: static, media, profiles, products, private-media. **Docelowo** (ADR 0025): `products` (public), `originals` (private), `documents` (private, presigned). Zdjęć profilowych nie ma.
- Pipeline zdjęć (ADR 0025): klient wysyła oryginał (≤ ~2000 px, ≤ 10 MB) + kadr `{x,y,w,h}`; Celery + Pillow: crop → 400/800/1600 WebP q80–85; rekord ze statusem processing/ready; klucz bez hosta/bucketa, URL składa serializer.
- PDF (ADR 0026): WeasyPrint z szablonu Django, bezpośrednio z taska; Pango/Cairo w obrazie workera. `django-weasyprint` — nie.

## Konwencje API (rozstrzygnięte 2026-09-19)

**W kodzie globalnie** (`core/settings/components/auth.py`, `core/api/`): paginacja, backendy filtrów, limity żądań i domyślna permisja. Limity trzymają historię w cache'u — `CACHES` wskazuje Redisa (`components/cache.py`, `REDIS_CACHE_URL`, domyślnie baza 1), bo pamięć procesu mnoży limit przez liczbę workerów. Reszta punktów niżej dotyczy widoków, które dopiero powstaną.

- Permisje: globalnie `IsAuthenticated` zostaje. `AllowAny` odczyt: products, categories, collections, aktywne promotions, shipping-methods. Koszyk gościa po `session_key`. Zapis własnych danych: zalogowany + queryset filtrowany po `request.user`. **Bez django-guardian.**
- Mutacje katalogu, promocji, kursów kruszcu, metod dostawy — **wyłącznie Django admin** (ADR 0021). Zero POST/PUT/DELETE na te zasoby w API. Staff nie ma osobnego API.
- Paginacja: `PageNumberPagination`, `page_size=24`, max 100. Mobile: `useInfiniteQuery` po `?page=N`; web: strony numerowane z URL. Cursor — nie, dopóki katalog nie liczy dziesiątek tysięcy.
- Filtry: `django-filter` po cechach z `choices` (material, fineness na Product; metal_color, size/length, stone na Variant), cena min/max, kategoria z potomkami, kolekcja; sort: cena / nowość / nazwa. Wyszukiwarka: Postgres `SearchVector`. **Bez tagów, bez Elasticsearch.**
- Slug: jeden, angielski, z nazwy EN przy publikacji, niezmienny (zmiana = 301). Web: Next i18n routing `/pl/` `/en/`, `NEXT_LOCALE`, hreflang, sitemap z API, OG, schema.org Product, robots.txt. Mobile: język z urządzenia, deep link `olivin://product/<slug>`.
- i18n interfejsu: pliki tłumaczeń web/mobile, poza bazą. Tłumaczenia treści katalogu: baza (`Translation`, ADR 0027).
- Throttling DRF (wbudowany): anon 60/min, user 300/min; osobny scope `auth` 10/min, włączany na widoku przez `throttle_scope` — czeka na logowanie i walidację kuponu. Stripe webhook: podpis + idempotencja przez `WebhookEvent`. Stripe Radar włączony. Limity: max 5 szt. na pozycję, gość max 10 000 zł (powyżej wymaga konta).
- Staff: TOTP obowiązkowe dla `is_staff` (allauth); e-mail do właściciela po aktywacji `MetalRate`; `LogEntry` admina jako audyt.
- Celery beat (`DatabaseScheduler` jest): tłumaczenia 24 h; rezerwacje co 5 min (TTL 30 min od Payment Intent); `pending` > 24 h → `cancelled` co 1 h; MetalRate miesięcznie → proposed; NBP dziennie; porzucone koszyki e-mail po 24 h (opt-in). `Watch` zdarzeniowo, nie cyklicznie.
- Analityka: Umami self-hosted (kontener + baza na tym samym Postgresie), bez cookies; baner web: „niezbędne” + „marketing” (off), bez „analityczne”. `apps/analytics` usunięta. Mobile: nic.
- Testy: backend pytest per app + factory_boy, markery, 60%; MSW w `packages/api` wspólny web+mobile; Playwright smoke web; Maestro smoke mobile (ADR 0020). Kolejność: backend → MSW → Playwright → Maestro.
- Paczki instalowane przy bilecie, nie z góry: backend `weasyprint`, `deepl`; frontend `msw`, `expo-notifications`, `expo-file-system`, `expo-sharing`, widget InPost (web script, mobile WebView). **Nie**: guardian, django-weasyprint, elasticsearch, GA, Plausible CE.

## Payments

- `stripe` w `pyproject.toml`, `apps/payments` **pusty**.
- **Brak** jakiejkolwiek zależności Stripe w `frontend/package.json`.
- Nie implementuj Stripe bez jawnego zadania.

## Integracje

Adaptery w **`core/integrations/`** (mail, allauth). Settings i Celery mogą jeszcze wskazywać legacy `core.services.*` — nowy kod pisz pod `core/integrations/`.

## Struktura katalogów (stan obecny)

**Frontend (`frontend/` = korzeń workspace'ów Bun):** `web/`, `mobile/`, `packages/{config,tokens,api,schemas,money}`, `turbo.json`, `bunfig.toml`, `bun.lock`.

**Mobile:** `app/` (routing Expo Router), `src/core/` (w tym `core/api/transport.ts` — wstrzyknięcie transportu), `src/features/`, `src/ui/`.

**Web:** `app/` (App Router: `layout.tsx`, `page.tsx`, `providers.tsx`, `globals.css`, generowany `tokens.css`), `src/lib/` (`http.ts`, `api-transport.ts`), `scripts/generate-tokens-css.mjs`.

**Klient API:** `frontend/packages/api/generated/` — **nie edytuj ręcznie**. Wejścia Orvala to pliki `backend/src/schema.yaml` i `backend/src/allauth-schema.json`, nie HTTP.

**Backend:** `core/`, `apps/`, `common/`, `schema.yaml`, `tests/` (centralnie, nie per-app `tests.py`).

**Tokeny designu:** `@olivin/tokens` — paleta robocza (brand/neutral/semantyczne), typografia, promienie, cienie, breakpointy. Adaptery: `mobile/tailwind.config.js` (v3) i `web/scripts/generate-tokens-css.mjs` → `web/app/tokens.css` (v4). Tożsamość wizualna marki **nie jest** jeszcze dobrana.

## CI (`.github/workflows/ci.yml`)

**Backend:** uv sync → Ruff → Pyrefly → `task db:migrations:check` → `task backend:schema:check` → `task test:backend-local -- src/ -m "not integration"`.

**Frontend:** bun frozen → ESLint → tsc → Prettier.

**Pre-commit:** osobny job uruchamiający te same hooki co `git commit`.

**Frontend w CI dodatkowo:** `task ovral:check` — rozjazd wygenerowanego klienta ze schematem zatrzymuje przepływ.

**Czego CI nie robi:** testów integracyjnych w Dockerze, żadnych testów frontendu (brak runnera), buildów EAS, buildu weba.

## Kontrole po zmianach

- Backend: `task test:backend-local -- <ścieżka>`, `task lints:backend:ruff:check`, `task lints:backend:typecheck`
- Frontend: `task lints:frontend:lint:check`, `task lints:frontend:typecheck`

## Co zostało z przebudowy

Wykonane: monorepo, web ze stroną główną, pakiety, bramka Orvala. **Niewykonane:** test przeglądarkowy (#55), web w docker-compose (#56), tożsamość wizualna (paleta w tokenach jest robocza).
