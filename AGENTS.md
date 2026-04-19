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
- `axios`,
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

### Backend

- Widoki i viewsety powinny być cienkie i orkiestracyjne.
- Logika biznesowa nie powinna być rozlana jednocześnie po serializerach, modelach i widokach.
- Walidację, permissions i bezpieczeństwo traktuj jako elementy obowiązkowe.
- Uważaj na N+1 queries oraz sensowne użycie `select_related` i `prefetch_related`.
- Zwracaj uwagę na atomowość operacji i side effecty.
- Jeśli zmieniasz kontrakt API, oceń wpływ na `backend/src/schema.yaml` i frontendowe typy lub klienty generowane przez Orval.

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
- nie uruchamiaj ciężkiego procesu planowania dla drobnej poprawki, jeśli lokalna diagnoza wystarcza.
