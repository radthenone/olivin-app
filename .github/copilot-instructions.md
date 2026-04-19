# GitHub Copilot Instructions for olivin-app

## Główny cel

Pomagaj w pracy nad repozytorium `olivin-app` zgodnie z realną strukturą projektu, zasadami clean architecture i repo-first workflow.
Jeśli projektujesz większą zmianę lub diagnozujesz obszerny błąd, uwzględnij kontekst zawarty w `docs/ai/architecture.md` oraz `docs/ai/workflow.md`.

## Zasady globalne

- Odpowiadaj po polsku.
- Pisz docstringi po polsku.
- Nazwy techniczne w kodzie pozostawiaj po angielsku.
- Najpierw analizuj repo, potem proponuj zmiany.
- Wskazuj konkretne pliki i ścieżki.
- Nie zakładaj istnienia plików lub warstw, których nie da się potwierdzić.
- Nie proponuj dużej przebudowy, jeśli wystarcza poprawka lokalna.

## Kontekst projektu

Projekt ma strukturę monorepo z frontendem Expo / React Native oraz backendem Django / DRF.

### Frontend

Pracuj z założeniem, że frontend znajduje się w `frontend/` i używa:

- Expo Router,
- TanStack Query,
- Zustand,
- React Hook Form,
- Zod,
- Axios,
- Orval,
- NativeWind.

W praktyce:

- `frontend/app/` obsługuje routing i layouty,
- `frontend/src/core/` zawiera fundamenty techniczne,
- `frontend/src/features/` zawiera logikę funkcjonalną,
- `frontend/src/api/` odpowiada za kontrakty i klienty,
- `frontend/src/ui/` zawiera współdzielone UI.

### Backend

Pracuj z założeniem, że backend znajduje się w `backend/` i używa:

- Django,
- Django REST Framework,
- allauth,
- SimpleJWT,
- Celery,
- Redis,
- Stripe,
- drf-spectacular,
- pytest,
- ruff.

W praktyce:

- `backend/src/core/` zawiera konfigurację i infrastrukturę,
- `backend/src/apps/` zawiera moduły domenowe,
- `backend/src/common/` zawiera elementy współdzielone,

## Zasady implementacyjne

### Frontend

- TanStack Query stosuj do server state.
- Zustand stosuj wyłącznie do local/app state.
- Nie przechowuj danych serwerowych w Zustand bez mocnego uzasadnienia.
- Nie mieszaj routingu, zapytań i UI w jednym miejscu, jeśli można to rozdzielić.
- Preferuj `async/await`.
- Używaj debounce do searcha, filtrów i wejść powodujących nadmiarowe requesty.
- Używaj lazy loading tam, gdzie faktycznie poprawia performance.
- Dbaj o stabilność hooków i unikaj zbędnych re-renderów.

### Backend

- Trzymaj widoki cienkie.
- Logikę biznesową trzymaj poza widokami.
- Nie rozlewaj odpowiedzialności po modelach, serializerach i viewsetach naraz.
- Pilnuj walidacji, permissions, bezpieczeństwa i atomowości operacji.
- Uważaj na wydajność zapytań ORM.
- Jeśli zmieniasz API, sprawdź wpływ na schema i frontendowy klient.

## Styl odpowiedzi

Jeśli analizujesz kod lub architekturę:

1. najpierw wskaż pliki,
2. potem opisz diagnozę,
3. potem podaj ryzyka,
4. na końcu zaproponuj plan zmian.

## Styl kodu

- Clean code.
- Czytelne nazwy.
- Małe moduły.
- Silne typowanie.
- Minimalna potrzebna abstrakcja.
- Bez ukrytych side effectów.
