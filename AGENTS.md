# AGENTS.md

## Cel pliku

Ten plik definiuje nadrzędne zasady pracy agentów AI w repozytorium `olivin-app`.
Ma być zrozumiały dla narzędzi i workflow opartych o `AGENTS.md`, dla pracy w stylu repo-first oraz dla agentów korzystających z podejścia skill-based podobnego do `obra/superpowers`.

## Priorytet instrukcji

Stosuj instrukcje w tej kolejności:

1. Bezpośrednie polecenie użytkownika.
2. Najbliższy kontekstowy plik `AGENTS.md`, jeśli istnieje bardziej lokalny.
3. Ten plik w root repo.
4. `.github/copilot-instructions.md` oraz pliki w `.github/instructions/` jako dodatkowe wskazówki dla Copilota i agentów IDE.
5. Zewnętrzne workflow i skille, w tym podejście inspirowane `obra/superpowers`.

**Ważne dla Agenta:** Jeśli zgłoszone zadanie dotyczy modyfikacji po stronie backendu, ZAWSZE najpierw przeczytaj `.github/instructions/backend.instructions.md`. Gdy polecenie dotyczy frontendu, najpierw zapoznaj się z `.github/instructions/frontend.instructions.md`.

Jeśli instrukcje są sprzeczne, pierwszeństwo ma poziom wyższy.

## Język i komunikacja

- ZAWSZE odpowiadaj po polsku, chyba że użytkownik wyraźnie poprosi o inny język.
- ZAWSZE pisz docstringi po polsku.
- Komentarze wyjaśniające, jeśli są potrzebne, także pisz po polsku.
- Nazwy techniczne w kodzie pozostawiaj po angielsku: nazwy zmiennych, funkcji, klas, typów, plików, endpointów, migracji i testów.
- Odpowiadaj konkretnie, technicznie i projektowo.
- Nie lej wody. Jeśli czegoś nie da się potwierdzić, napisz to wprost.

## Zasada nadrzędna: repo first

Przy każdym pytaniu technicznym i każdej propozycji zmian:

1. Najpierw przeanalizuj realną strukturę repozytorium.
2. Wskaż konkretne pliki i ścieżki związane z problemem.
3. Oddziel to, co potwierdzone, od tego, czego nie udało się potwierdzić.
4. Dopiero potem przedstaw diagnozę, ryzyka i plan zmian.
5. Nie zakładaj istnienia plików, warstw ani wzorców, których nie widać.

## Kontekst projektu

`olivin-app` jest projektem full-stack w układzie monorepo.

Szybkie źródła kontekstu:

- `README.md` — start developerski i najważniejsze taski,
- `docs/ai/architecture.md` — opis warstw i odpowiedzialności,
- `docs/ai/workflow.md` — sposób pracy agentów AI,
- `.github/instructions/backend.instructions.md` — reguły dla `backend/**`,
- `.github/instructions/frontend.instructions.md` — reguły dla `frontend/**`.

### Frontend

Frontend znajduje się w `frontend/` i jest oparty o Expo / React Native, nie o klasyczne React SPA w przeglądarce.

Potwierdzone obszary:

- `frontend/app/` — routing i layouty oparte o Expo Router,
- `frontend/src/core/` — fundamenty techniczne, np. auth, api, env, theme,
- `frontend/src/features/` — moduły funkcjonalne,
- `frontend/src/api/` — klienty i typy generowane z kontraktu,
- `frontend/src/ui/` — współdzielone komponenty UI.

Potwierdzone biblioteki i podejścia:

- `expo-router`,
- `@tanstack/react-query`,
- `zustand`,
- `react-hook-form`,
- `zod`,
- `orval`,
- `nativewind`.

### Backend

Backend znajduje się w `backend/` i jest oparty o Django + DRF.

Potwierdzone obszary:

- `backend/src/core/` — konfiguracja, settings, urls, celery, envs, storage,
- `backend/src/apps/` — domeny biznesowe,
- `backend/src/common/` — współdzielone abstrakcje,
- `backend/src/schema.yaml` — kontrakt API.

Potwierdzone biblioteki i podejścia:

- `django`,
- `djangorestframework`,
- `django-allauth`,
- `djangorestframework-simplejwt`,
- `celery`,
- `redis`,
- `stripe`,
- `drf-spectacular`,
- `pytest`,
- `ruff`.

## Komendy i środowisko uruchomieniowe

### Taskfile — obowiązkowy punkt wejścia do poleceń

Projekt używa [Taskfile](https://taskfile.dev/) jako głównego interfejsu do poleceń deweloperskich.
Główny plik: `Taskfile.yml` w root repo — importuje moduły z `taskfiles/`.

**Zasada:** jeśli potrzebujesz zaproponować albo uruchomić komendę (migracja, test, shell, build, paczki, generowanie API, frontend), najpierw sprawdź `Taskfile.yml` oraz właściwy plik w `taskfiles/`. Preferuj `task <namespace>:<nazwa>` zamiast bezpośrednich wywołań.

Jeśli nie pamiętasz nazwy taska, użyj lub zaproponuj `task --list`.
Jeśli środowisko agenta nie ma lokalnie `task`, `bun`, `uv` albo Dockera w `PATH`, napisz to wprost i podaj równoważną komendę taskową do wykonania przez użytkownika.

Dostępne namespace'y i przykłady:

| Namespace | Plik | Przykładowe taski |
|-----------|------|-------------------|
| `backend` | `taskfiles/backend.yml` | `task backend:run`, `task backend:build`, `task backend:logs`, `task backend:clean-docker` |
| `db` | `taskfiles/db.yml` | `task db:migrate`, `task db:migrations:make -- <app>`, `task db:migrations:rollback -- <app> <nr>`, `task db:clean:volumes` |
| `test` | `taskfiles/test.yml` | `task test:backend`, `task test:backend-local -- <ścieżka>`, `task test:backend-local-unit -- <ścieżka>`, `task test:backend-integration -- <ścieżka>`, `task test:backend-cmd -- <ścieżka>`, `task test:backend-down` |
| `shell` | `taskfiles/shell.yml` | `task shell:run`, `task shell:run:plus` |
| `frontend` | `taskfiles/frontend.yml` | `task frontend:run`, `task frontend:run:clear`, `task frontend:metro`, `task frontend:metro:clear`, `task frontend:build:android`, `task frontend:prebuild:clean` |
| `packages` | `taskfiles/packages.yml` | `task packages:backend:add -- <pkg>`, `task packages:frontend:add -- <pkg>` |
| `ovral` | `taskfiles/ovral.yml` | `task ovral:generate`, `task ovral:watch` |
| `emulator` | `taskfiles/emulators.yml` | `task emulator:run` |
| `lints` | `taskfiles/lints.yml` | `task lints:backend:ruff`, `task lints:backend:ruff:check`, `task lints:backend:typecheck`, `task lints:frontend:lint`, `task lints:frontend:lint:check`, `task lints:frontend:typecheck`, `task lints:frontend:format`, `task lints:frontend:format:check` |

**Uwaga:** namespace `ovral` jest nazwą taska w repo, ale dotyczy narzędzia Orval. Nie edytuj ręcznie plików w `frontend/src/api/generated/**`; po zmianach API generuj klienta przez `task ovral:generate`.

**Ważne:** Gdy task przyjmuje argumenty, przekazuj je po `--` zgodnie z konwencją Taskfile, np. `task db:migrations:make -- accounts`.

### Komendy kontrolne po zmianach

Dobieraj najmniejszy sensowny zestaw kontroli do zakresu zmiany:

- backend szybki: `task test:backend-local -- <ścieżka>`,
- backend jednostkowy: `task test:backend-local-unit -- <ścieżka>`,
- backend integracyjny: `task test:backend-integration -- <ścieżka lub marker>`,
- backend pełny w Dockerze: `task test:backend`,
- backend lint i format Ruff z poprawkami: `task lints:backend:ruff`,
- backend lint i format Ruff bez zmian w plikach: `task lints:backend:ruff:check`,
- backend typecheck: `task lints:backend:typecheck`,
- frontend lint z poprawkami: `task lints:frontend:lint`,
- frontend lint bez zmian w plikach: `task lints:frontend:lint:check`,
- frontend typecheck: `task lints:frontend:typecheck`,
- frontend format: `task lints:frontend:format`,
- frontend format check: `task lints:frontend:format:check`.

Jeśli środowisko nie pozwala uruchomić kontroli, napisz wprost, których tasków nie udało się wykonać i dlaczego.

### Shell — bash, nie PowerShell

Wszystkie komendy shellowe w tym projekcie zakładają **bash**. Skrypty w `scripts/`, komendy w taskfilach i entrypointy kontenerów pisane są w bash.

- Używaj składni bash: `&&`, `||`, `$()`, `find ... | xargs`, itp.
- Nie proponuj składni PowerShell ani cmd.exe.
- Jeśli musisz uruchomić bash w środowisku Windows, używaj WSL lub Git Bash.

### Docker Compose — kontenery projektu

Plik: `docker-compose.yml` (dev), `docker-compose.test.yml` (testy).

Kontenery zdefiniowane w `docker-compose.yml`:

| Nazwa kontenera | Obraz | Rola | Profile |
|-----------------|-------|------|---------|
| `olivin-postgres` | `postgres:16` | Baza danych PostgreSQL (port `5434:5432`) | `dev`, `backend`, `full`, `local` |
| `olivin-redis` | `redis:latest` | Cache i broker Celery | `dev`, `backend`, `full`, `local`, `test` |
| `olivin-minio` | `minio/minio:latest` | Obiektowy storage S3-compatible | `dev`, `backend`, `full`, `local`, `test` |
| `olivin-mailhog` | `mailhog/mailhog` | Lokalny SMTP do testowania maili | `dev`, `backend`, `full`, `local` |
| `olivin-django` | custom (Dockerfile) | Serwer Django / DRF | `dev`, `backend`, `full` |
| `olivin-celery-worker` | custom (Dockerfile) | Celery worker | `dev`, `backend`, `full`, `celery` |
| `olivin-celery-beat` | custom (Dockerfile) | Celery beat (scheduler) | `dev`, `backend`, `full`, `celery` |
| `olivin-celery-flower` | custom (Dockerfile) | Flower — UI monitora Celery | `dev`, `backend`, `full`, `celery` |

Wszystkie kontenery działają w sieci `olivin-network` (zewnętrzna sieć Docker).
Volumeny: `olivin-data` (PostgreSQL), `olivin-media` (MinIO).

**Aby exec-ować komendę w kontenerze Django:** `docker exec -it olivin-django <komenda>`
Albo przez odpowiedni task, np. `task db:migrate`.

## Zasady architektoniczne

### Zasady ogólne

- Preferuj lokalną, najmniejszą sensowną zmianę zamiast dużego refaktoru.
- Pilnuj separation of concerns.
- Pilnuj silnego typowania.
- Projektuj małe, czytelne moduły.
- Nie mieszaj warstw odpowiedzialności.
- Zwracaj uwagę na testowalność, naming, performance, bezpieczeństwo i ryzyko regresji.
- Nie dodawaj abstrakcji bez realnej potrzeby.

### Frontend

- TanStack Query służy do server state.
- Zustand służy tylko do local/app state.
- Nie przenoś danych serwerowych do Zustand, jeśli nie ma bardzo mocnego uzasadnienia.
- Routing zostaw w `frontend/app/`.
- Logikę funkcjonalną trzymaj w `frontend/src/features/`.
- Fundamenty techniczne trzymaj w `frontend/src/core/`.
- Nie wywołuj API bezpośrednio w komponentach, jeśli logika powinna być zamknięta w hooku, serwisie lub warstwie api.
- Preferuj `async/await` zamiast nadmiernego chainowania promise.
- Stosuj debounce tam, gdzie ogranicza zbędne requesty.
- Stosuj lazy loading tam, gdzie realnie poprawia performance lub ogranicza koszt wejścia do ciężkich ekranów.
- Cache konfiguruj świadomie zgodnie z naturą danych i UX.
- Uważaj na zbędne re-rendery, efekty uboczne i niestabilne zależności hooków.
- Wygenerowane klienty i typy API trzymaj w `frontend/src/api/generated/`; nie edytuj ich ręcznie.
- Niskopoziomową mechanikę sesji allauth trzymaj w `frontend/src/core/auth/`.
- Flow logowania, rejestracji, weryfikacji email, resetu hasła i MFA trzymaj w `frontend/src/features/auth/`.
- Dane konta zalogowanego użytkownika, profil, adresy i ustawienia bezpieczeństwa trzymaj w `frontend/src/features/account/`.
- Wspólne komponenty UI trzymaj w `frontend/src/ui/`; różnice web/native rozwiązuj przez pliki `.web/.native` albo helpery w `frontend/src/ui/platform/`.
- Dla stylu shadcn-like w Expo / React Native preferuj lokalne primitives + NativeWind + `class-variance-authority`, nie DOM-only komponenty z klasycznego `shadcn/ui`.

### Backend

- Widoki i viewsety powinny być cienkie i orkiestracyjne.
- Logika biznesowa nie powinna być rozlana jednocześnie po serializerach, modelach i widokach.
- Walidację, permissions i bezpieczeństwo traktuj jako elementy obowiązkowe.
- Uważaj na N+1 queries oraz sensowne użycie `select_related` i `prefetch_related`.
- Zwracaj uwagę na atomowość operacji i side effecty.
- Jeśli zmieniasz kontrakt API, oceń wpływ na `backend/src/schema.yaml` i frontendowe typy lub klienty generowane przez Orval.
- Jeśli zmieniasz serializer, viewset, URL albo schema endpointu, po zmianie zaplanuj `task ovral:generate` oraz kontrolę `task lints:frontend:typecheck`.

## Jak odpowiadać

W odpowiedziach technicznych stosuj ten format, jeśli temat dotyczy kodu lub architektury:

1. Krótka diagnoza.
2. Co dokładnie znaleziono w repo.
3. Lista problemów, ryzyk lub ograniczeń.
4. Rekomendowany plan zmian krok po kroku.
5. Jeśli ma sens: propozycja implementacji lub refaktoru.
6. Jeśli czegoś nie dało się potwierdzić z repo, napisz to wprost.

## Jak korzystać z workflow podobnego do superpowers

Workflow inspirowany `obra/superpowers` ma pomagać w sposobie pracy, ale nie zastępuje wiedzy o tym projekcie.

W praktyce:

- dla bugfixów najpierw ustal objaw, potem przyczynę źródłową, potem minimalną poprawkę,
- dla feature najpierw ustal miejsce w architekturze, potem zakres zmian FE/BE/API,
- dla refaktoru najpierw nazwij problem jakościowy, potem zaproponuj najmniejszy sensowny refaktor,
- nie uruchamiaj ciężkiego procesu planowania dla drobnej poprawki, jeśli lokalna diagnoza wystarcza,
- gdy proponujesz komendę do wykonania, **zawsze najpierw sprawdź Taskfile** — jeśli istnieje odpowiedni task, użyj go zamiast surowego docker/bash,
- komendy shellowe pisz w **bash**, nie w PowerShell,
- gdy odwołujesz się do kontenera lub serwisu, używaj nazw z sekcji Docker Compose powyżej.

## Higiena repozytorium

- Nie commituj lokalnych cache'y, coverage, logów, plików `.env`, `.venv`, `node_modules`, `.expo`, `mediafiles`, `staticfiles` ani build outputów.
- Nie edytuj ręcznie plików w `frontend/src/api/generated/**`.
- Jeśli repo ma dużo zmian roboczych, przed większą analizą nazwij ten fakt i uważaj, by nie cofnąć cudzych zmian.
- Przy zmianach API pamiętaj o sekwencji: backend schema → `task ovral:generate` → `task lints:frontend:typecheck`.
