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
- `backend/src/apps/categories` — `Category` jako drzewo (rodzic jako klucz obcy do siebie, bez mptt), slug niezmienny, narzut domyślny. Panel do edycji, API **tylko do odczytu**: `GET /categories/` (drzewo zagnieżdżone, bez stronicowania) i `GET /categories/<slug>/`, oba `AllowAny`. Testy w `backend/src/tests/categories/`.
- `backend/src/apps/translations` — `Translation` (model źródłowy i pole, język, tekst, źródło `auto`/`manual`) jako relacja generyczna na produkcie, zdjęciu, kategorii i kolekcji. Dwa wyzwalacze: publikacja produktu i obchód beat co 24 h; automat nigdy nie nadpisuje poprawki ręcznej. API katalogu przyjmuje `?lang=` i `Accept-Language`, z odwrotem na polski; slug nie jest tłumaczony. Testy w `backend/src/tests/translations/`.
- `backend/src/apps/collections` — `Collection` (nazwa PL, slug niezmienny, relacja wiele-do-wielu z produktami). Panel z `filter_horizontal`, API **tylko do odczytu**: `GET /collections/` i `GET /collections/<slug>/`, `AllowAny`, wyłącznie kolekcje z co najmniej jednym opublikowanym produktem. Produkty kolekcji przez `GET /products/?collection=<slug>`. Testy w `backend/src/tests/collections/`.
- `backend/src/apps/products` — `Product` (status `draft`/`published`, kategoria-liść, materiał i próba jako `choices`, flaga produktu na zamówienie z czasem realizacji, flaga grawerunku `is_engravable` z ceną `engraving_price` w groszach — jedno wymaga drugiego, ADR 0018) oraz `ProductVariant` (SKU, kolor kruszcu, rozmiar/długość, kamień, masa kruszcu, `price` i `manual_price` jako grosze, stawka VAT albo zwolnienie z podstawą prawną). Panel z wariantami inline i akcją publikacji; API **tylko do odczytu**: `GET /products/` (opublikowane, każdy z najtańszym wariantem; filtry cech, zakres ceny, kategoria z potomkami, sortowanie `?ordering=`, wyszukiwarka `?search=`) i `GET /products/<slug>/`, oba `AllowAny`. `Gemstone` 0..n przy wariancie (rodzaj, karaty, czystość, barwa, szlif, certyfikat PDF w buckecie `documents` z adresem podpisanym na czas). `ProductImage`: oryginał w buckecie `originals`, kadr `{x,y,width,height}`, zadanie Celery z Pillow tnie i zapisuje 400/800/1600 WebP w `products`; zdjęcie w `processing` nie wychodzi przez API. Wycena ze wzoru (ADR 0022) w `apps/products/pricing.py`: `MetalRate` z cyklem `proposed`/`active`/`archived`, `CostComponent` przy wariancie, marża wariantu nadpisująca marżę kategorii, próg kosztowy. Aktywacja kursu jest akcją w panelu — archiwizuje poprzedni kurs, kolejkuje przeliczenie cen i wysyła wiadomość do właściciela. Testy w `backend/src/tests/products/`.
- `backend/src/apps/consents` — `ConsentDocument` (rodzaj `terms`/`privacy`/`marketing`, wersja unikalna w rodzaju, data obowiązywania; bieżąca = najnowsza już obowiązująca) i `Consent` (użytkownik XOR e-mail gościa, dokument, kopia wersji, data; constraint w bazie). `Consent.objects.has_current_consent(kind, user=|email=)` zwraca `False` po nowej wersji dokumentu. API: `GET /consents/documents/` (bieżące wersje, `AllowAny`, bez stronicowania) i `POST /consents/` (zalogowany na konto, gość po `email`; dokument musi być bieżący). Rejestracja **nie** wymaga zgody — wymuszenie przyjdzie z zamówieniem i osobnym biletem dla rejestracji. Testy w `backend/src/tests/consents/`.
- `backend/src/apps/inventory` — `InventoryItem` (rezerwacje) i `StockMovement` (zmiana z przyczyną). Stan to **suma ruchów**, nie kolumna; ruch zapisany jest nieedytowalny, korektę robi się kolejnym ruchem. Panel prowadzi magazyn, API go nie wystawia — dostępność wychodzi tylko jako `available` / `isAvailable` / `isLowStock` na wariancie. Produkt na zamówienie nie ma stanu i jest dostępny zawsze (ADR 0024). Testy w `backend/src/tests/products/test_inventory.py`.
- `backend/src/core/` — settings (django-split-settings), integracje, storage, utils. Health check: **`GET /health/`** (nie pod `/api/`), zwraca stan bazy, Redisa i storage.
- `backend/src/apps/shipping` — `ShippingMethod` (rodzaj `parcel_locker`/`courier`/`pickup`/`eu`, strefa `PL`/`EU`, stała stawka, górna wartość zamówienia jako `max_order_value`, aktywność). Ubezpieczenia nie ma w modelu — jest wliczone w stawkę (ADR 0028). Odbiór osobisty bez limitu pilnuje ograniczenie w bazie. Próg darmowej dostawy to **ustawienie** `FREE_SHIPPING_THRESHOLD` (grosze, `core/settings/components/shop.py`), nie model. API **tylko do odczytu**: `GET /shipping-methods/?order_value=&zone=`, `AllowAny`, bez stronicowania — metody z kosztem policzonym dla wartości koszyka; metoda w innej walucie niż koszyk jest odfiltrowana, nie zgłaszana błędem. Mutacje wyłącznie w panelu (ADR 0021). Testy w `backend/src/tests/shipping/`.
- `backend/src/common/` — pola, modele bazowe w tym `TranslatableModel`, lokalizacja, pieniądze (`money/`) i slugi katalogu (`slugs.py`).
- `frontend/mobile/` — aplikacja Expo: ekrany auth (logowanie, rejestracja, MFA, weryfikacja e-mail, reset hasła, logowanie kodem), konto, profil.
- `frontend/web/` — aplikacja Next.js 16 (App Router, Tailwind v4). **Jedna trasa**: strona główna ze stanem zdrowia backendu. Zero ekranów sklepu.
- `frontend/packages/` — `@olivin/config` (tsconfig, eslint, prettier, loader env), `@olivin/tokens` (tokeny designu, CommonJS + d.ts), `@olivin/api` (klient Orval obu schematów + kontrakt transportu), `@olivin/schemas` i `@olivin/money` (**puste** szkielety).

**Puste szkielety po `startapp` — dziewięć linii kodu każdy, zero modeli, zero migracji:**

`orders`, `payments`, `discounts`, `reviews`, `notifications`

Nie zakładaj, że którakolwiek z nich cokolwiek zawiera. Nie ma modelu Order, nie ma Cart, nie ma stanu magazynowego.

**Nie istnieje po stronie frontendu:** `features/catalog`, `features/cart`, `features/checkout`, `features/orders`, `features/payments`. Są tylko `auth`, `account`, `profile`.

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
| `FREE_SHIPPING_THRESHOLD` | **50000** groszy — próg darmowej dostawy wspólny dla sklepu (`components/shop.py`); pusta wartość wyłącza |

Zmienne ładowane z `.env` oraz `.envs/dev/**` przez `dotenv:` w `Taskfile.yml`.

## Docker Compose (dev)

`docker-compose.yml` definiuje **dziewięć** usług backendu (plus `olivin-web`):

`olivin-postgres` (PostgreSQL 16), `olivin-redis` (cache + broker), `olivin-minio` (S3-compatible), `olivin-mailhog` (SMTP dev), `olivin-libretranslate` (silnik tłumaczeń, `LT_LOAD_ONLY=pl,en`), `olivin-django`, `olivin-celery-worker`, `olivin-celery-beat`, `olivin-celery-flower`.

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

`APPS_TAGS` w `frontend/packages/api/orval.config.js` (obecnie): **`Addresses`, `Categories`, `Collections`, `Consents`, `Products`, `Profiles`, `Shipping`, `Health`**. Nowy viewset domenowy bez dopisania tagu nie trafi do klienta — cichy błąd.

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

- **Brak `apps/files`.** Storage w `backend/src/core/storage/` — MinIO w dev, S3 w prod przez `USE_AWS`. Model trzyma **sam klucz obiektu**, bez hosta i bucketa; adres składa `core.storage.object_url` w warstwie serializacji.
- Buckety (ADR 0025, `core/storage/buckets.py`): `products` (odczyt publiczny), `originals` (prywatny), `documents` (prywatny, adres podpisany na czas). Nazwy przez `S3_BUCKET_PRODUCTS` / `S3_BUCKET_ORIGINALS` / `S3_BUCKET_DOCUMENTS`, czas ważności podpisu przez `S3_SIGNED_URL_TTL`. Zdjęć profilowych nie ma; pliki statyczne Django nie mają bucketa. Bootstrap: `sync_buckets()` z `docker/scripts/backend/init-minio.sh` — zakłada i nakłada polityki, **niczego nie kasuje**.
- Pipeline zdjęć (ADR 0025): klient wysyła oryginał (≤ ~2000 px, ≤ 10 MB) + kadr `{x,y,w,h}`; Celery + Pillow: crop → 400/800/1600 WebP q80–85; rekord ze statusem processing/ready; klucz bez hosta/bucketa, URL składa serializer.
- PDF (ADR 0026): WeasyPrint z szablonu Django, bezpośrednio z taska; Pango/Cairo w obrazie workera. `django-weasyprint` — nie.

## Konwencje API (rozstrzygnięte 2026-09-19)

**W kodzie globalnie** (`core/settings/components/auth.py`, `core/api/`): paginacja, backendy filtrów, limity żądań i domyślna permisja. Limity trzymają historię w cache'u — `CACHES` wskazuje Redisa (`components/cache.py`, `REDIS_CACHE_URL`, domyślnie baza 1), bo pamięć procesu mnoży limit przez liczbę workerów. Reszta punktów niżej dotyczy widoków, które dopiero powstaną.

- Permisje: globalnie `IsAuthenticated` zostaje. `AllowAny` odczyt: products, categories, collections, aktywne promotions, shipping-methods. Koszyk gościa po `session_key`. Zapis własnych danych: zalogowany + queryset filtrowany po `request.user`. **Bez django-guardian.**
- Mutacje katalogu, promocji, kursów kruszcu, metod dostawy — **wyłącznie Django admin** (ADR 0021). Zero POST/PUT/DELETE na te zasoby w API. Staff nie ma osobnego API.
- Paginacja: `PageNumberPagination`, `page_size=24`, max 100. Mobile: `useInfiniteQuery` po `?page=N`; web: strony numerowane z URL. Cursor — nie, dopóki katalog nie liczy dziesiątek tysięcy.
- Filtry: `django-filter` po cechach z `choices` (material, fineness na Product; metal_color, size/length, stone na Variant), cena min/max, kategoria z potomkami, kolekcja; sort: cena / nowość / nazwa. Wyszukiwarka: Postgres `SearchVector`. **Bez tagów, bez Elasticsearch.** Testy jednostkowe chodzą na SQLite, więc wyszukiwarka ma szew (`apps/products/search.py`): pełny tekst na PostgreSQL, dopasowanie po fragmencie poza nim. Gałąź postgresową pokrywa test z markerem `integration`.
- Slug: jeden, angielski, z nazwy EN przy publikacji, niezmienny (zmiana = 301) — **w kodzie**: `common/slugs.py` bierze angielskie brzmienie z `Translation`, a nie z nazwy polskiej bez ogonków. Slug wpisany w panelu ma pierwszeństwo i nie rusza silnika. Bez angielskiej nazwy zapis jest odrzucany, nigdy nie ma cichego odwrotu do polskiego. Produkt dostaje adres dopiero przy publikacji — szkic ma `slug = NULL`. Web: Next i18n routing `/pl/` `/en/`, `NEXT_LOCALE`, hreflang, sitemap z API, OG, schema.org Product, robots.txt. Mobile: język z urządzenia, deep link `olivin://product/<slug>`.
- i18n interfejsu: pliki tłumaczeń web/mobile, poza bazą. Tłumaczenia treści katalogu: baza (`Translation`, ADR 0027) — **w kodzie**, silnik przez `TRANSLATION_PROVIDER` (domyślnie LibreTranslate — usługa jest w `docker-compose.yml`; produkcja DeepL).
- Throttling DRF (wbudowany): anon 60/min, user 300/min; osobny scope `auth` 10/min, włączany na widoku przez `throttle_scope` — czeka na logowanie i walidację kuponu. Stripe webhook: podpis + idempotencja przez `WebhookEvent`. Stripe Radar włączony. Limity: max 5 szt. na pozycję, gość max 10 000 zł (powyżej wymaga konta).
- Staff: TOTP obowiązkowe dla `is_staff` (allauth); e-mail do właściciela po aktywacji `MetalRate`; `LogEntry` admina jako audyt.
- Celery beat (`DatabaseScheduler` jest; aplikacja Celery ładowana z `core/__init__.py`): `propose_metal_rates` pierwszego dnia miesiąca i `translate_published_catalog` co 24 h — **w kodzie**; rezerwacje co 5 min (TTL 30 min od Payment Intent); `pending` > 24 h → `cancelled` co 1 h; MetalRate miesięcznie → proposed; NBP dziennie; porzucone koszyki e-mail po 24 h (opt-in). `Watch` zdarzeniowo, nie cyklicznie.
- Analityka: Umami self-hosted (kontener + baza na tym samym Postgresie), bez cookies; baner web: „niezbędne” + „marketing” (off), bez „analityczne”. `apps/analytics` usunięta. Mobile: nic.
- Testy: backend pytest per app + factory_boy, markery, 60%; MSW w `packages/api` wspólny web+mobile; Playwright smoke web; Maestro smoke mobile (ADR 0020). Kolejność: backend → MSW → Playwright → Maestro.
- Paczki instalowane przy bilecie, nie z góry: backend `weasyprint`, `deepl`; frontend `msw`, `expo-notifications`, `expo-file-system`, `expo-sharing`, widget InPost (web script, mobile WebView). **Nie**: guardian, django-weasyprint, elasticsearch, GA, Plausible CE.

## Payments

- `stripe` w `pyproject.toml`, `apps/payments` **pusty**.
- **Brak** jakiejkolwiek zależności Stripe w `frontend/package.json`.
- Nie implementuj Stripe bez jawnego zadania.

## Integracje

Adaptery w **`core/integrations/`** — kurs kruszcu (`metal_rate/`, dostawca przez `METAL_RATE_PROVIDER`, domyślnie zastępczy `LastActiveRateProvider`, ADR 0027). Mail i allauth siedzą jeszcze w legacy `core.services.*` — nowy kod pisz pod `core/integrations/`.

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
