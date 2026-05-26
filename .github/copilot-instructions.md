# GitHub Copilot Instructions for olivin-app

## Źródła Prawdy

To repo działa w trybie repo-first. Przed techniczną odpowiedzią sprawdź realne pliki i taski.

Najważniejsze dokumenty:

- `AGENTS.md` — nadrzędne zasady dla agentów AI,
- `docs/ai/architecture.md` — architektura i odpowiedzialności warstw,
- `docs/ai/workflow.md` — tryby pracy: bugfix, feature, refactor, documentation/workflow,
- `.github/instructions/backend.instructions.md` — reguły dla `backend/**`,
- `.github/instructions/frontend.instructions.md` — reguły dla `frontend/**`,
- `Taskfile.yml` i `taskfiles/*.yml` — źródło prawdy dla komend.

Jeśli instrukcje są sprzeczne, ważniejszy jest bezpośredni request użytkownika, potem `AGENTS.md`, potem lokalne instrukcje `.github/instructions/*`.

## Język

- Odpowiadaj po polsku.
- Docstringi i komentarze wyjaśniające pisz po polsku.
- Nazwy techniczne w kodzie zostaw po angielsku.

## Projekt

`olivin-app` to monorepo:

- `backend/` — Django + Django REST Framework,
- `frontend/` — Expo / React Native z Expo Router,
- `taskfiles/` — komendy developerskie przez Taskfile,
- `docs/ai/` — dokumentacja dla ludzi i agentów AI.

Frontend nie jest klasycznym React SPA. Nie zakładaj DOM-only API ani komponentów web-only, jeśli repo tego nie potwierdza.

## Backend

Główne katalogi:

- `backend/src/core/` — konfiguracja, settings, urls, celery, infrastruktura,
- `backend/src/apps/` — domeny biznesowe,
- `backend/src/common/` — współdzielone abstrakcje,
- `backend/src/tests/` — testy.

Zasady:

- Widoki i viewsety powinny być cienkie.
- Logika biznesowa nie powinna być rozlana po modelach, serializerach i widokach naraz.
- Pilnuj walidacji, permissions, atomowości, side effectów i ryzyka N+1.
- Po zmianie API uwzględnij schema, Orval i frontendowy typecheck.

## Frontend

Główne katalogi:

- `frontend/app/` — routing i layouty Expo Router,
- `frontend/src/core/` — auth, config, http, query, theme, navigation,
- `frontend/src/features/` — moduły funkcjonalne,
- `frontend/src/api/` — klienty i typy generowane,
- `frontend/src/ui/` — współdzielone UI.

Zasady:

- TanStack Query służy do server state.
- Zustand służy tylko do local/app state.
- Nie wywołuj API bezpośrednio w dużych komponentach ekranowych, jeśli logika powinna być w hooku, serwisie albo warstwie feature.
- Nie edytuj ręcznie `frontend/src/api/generated/**`.
- Różnice web/native rozwiązuj przez pliki `.web/.native` albo helpery w `frontend/src/ui/platform/`.

## Komendy

Zawsze najpierw sprawdź `Taskfile.yml` i właściwy plik w `taskfiles/`.
Preferuj `task <namespace>:<nazwa>` zamiast surowych wywołań.
Argumenty przekazuj po `--`.

Najczęstsze taski:

- `task backend:run`
- `task backend:build`
- `task db:migrate`
- `task test:backend-local -- <ścieżka>`
- `task test:backend`
- `task lints:backend:ruff`
- `task lints:backend:ruff:check`
- `task lints:backend:typecheck`
- `task frontend:run`
- `task frontend:run:clear`
- `task lints:frontend:lint`
- `task lints:frontend:lint:check`
- `task lints:frontend:typecheck`
- `task lints:frontend:format`
- `task lints:frontend:format:check`
- `task ovral:generate`

Komendy shellowe w projekcie zapisuj w bash, nie w PowerShell.

## Kontrakt API

Jeśli zmieniasz serializer, viewset, URL, schema endpointu albo strukturę odpowiedzi:

1. Oceń wpływ na `backend/src/schema.yaml`.
2. Uruchom lub zaplanuj `task ovral:generate`.
3. Uruchom lub zaplanuj `task lints:frontend:typecheck`.

## Styl Odpowiedzi

Przy pytaniach technicznych:

1. Wskaż powiązane pliki.
2. Podaj krótką diagnozę.
3. Wypisz ryzyka lub ograniczenia.
4. Zaproponuj plan albo wykonaj małą, lokalną zmianę.
5. Napisz, czego nie udało się potwierdzić.

Nie zakładaj istnienia warstw, plików ani wzorców, których repo nie potwierdza.
