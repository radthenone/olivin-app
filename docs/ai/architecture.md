# Architektura AI dla olivin-app

## Cel dokumentu

Ten dokument opisuje architekturę projektu `olivin-app` w sposób użyteczny dla człowieka i dla narzędzi AI.
Nie jest to pełna dokumentacja produktu. To jest techniczny opis struktury repo, odpowiedzialności warstw i zasad projektowych, których należy pilnować podczas analizy i zmian w kodzie.

## Kontekst repozytorium

Projekt ma układ monorepo z wyraźnym rozdziałem na frontend i backend.
Na poziomie root repo znajdują się m.in. katalogi:

- `frontend/`
- `backend/`
- `docker/`
- `scripts/`
- `taskfiles/`

To oznacza, że instrukcje i zmiany powinny być zawsze osadzone w konkretnej części projektu, a nie formułowane jako ogólne rady niezależne od struktury repo.

## Frontend

Frontend znajduje się w `frontend/` i jest oparty o Expo / React Native.
To ważne, bo nie należy traktować go jak zwykłej aplikacji React SPA działającej wyłącznie w przeglądarce.

### Główne obszary

- `frontend/app/` — routing i layouty w oparciu o Expo Router,
- `frontend/src/core/` — fundamenty techniczne, np. auth, api, env, theme,
- `frontend/src/features/` — moduły funkcjonalne i logika domenowa,
- `frontend/src/api/` — klient i typy oparte o kontrakt API,
- `frontend/src/ui/` — współdzielone komponenty UI.

### Zasady pracy na frontendzie

- Server state powinien być prowadzony przez TanStack Query.
- Zustand powinien służyć tylko do local/app state.
- Routing nie powinien być mieszany z logiką feature.
- Komponenty ekranowe nie powinny przejmować całej odpowiedzialności za fetchowanie, walidację, nawigację i rendering naraz.
- Debounce, lazy loading i cache należy stosować świadomie, a nie automatycznie.

## Backend

Backend znajduje się w `backend/` i jest oparty o Django + DRF.

### Główne obszary

- `backend/src/core/` — konfiguracja i infrastruktura,
- `backend/src/apps/` — moduły domenowe,
- `backend/src/common/` — elementy współdzielone,

### Zasady pracy na backendzie

- Widoki i viewsety powinny być cienkie.
- Logika biznesowa nie powinna być rozproszona po wielu warstwach.
- Należy pilnować walidacji, permissions, bezpieczeństwa i atomowości operacji.
- Należy uważać na wydajność ORM i ryzyko N+1 queries.
- Zmiany w API powinny uwzględniać wpływ na schema i frontendowe klienty.

## Integracja frontend-backend

Frontend i backend są spięte przez kontrakt API.
W praktyce oznacza to, że zmiana backendowego endpointu, schematu odpowiedzi lub walidacji może wymagać aktualizacji kontraktu i klienta po stronie frontendu.

Najważniejsza zasada:

- nie analizuj zmian tylko lokalnie w jednej warstwie, jeśli problem lub feature dotyka przepływu danych między frontendem i backendem.

## Reguły projektowe

- Preferuj małe, lokalne i przewidywalne zmiany.
- Nie mieszaj warstw odpowiedzialności.
- Nie buduj równoległej architektury obok istniejącej.
- Jeśli czegoś nie potwierdza repo, nie zakładaj tego jako faktu.
- Odpowiedzi techniczne i docstringi powinny być po polsku.
- Nazewnictwo techniczne w kodzie pozostaje po angielsku.
