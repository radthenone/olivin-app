---
applyTo: "frontend/**"
---

# Frontend instructions — olivin-app

## Zakres

Te instrukcje dotyczą zmian w `frontend/**`.

## Kontekst technologiczny

Frontend to Expo / React Native oparty o Expo Router.
Najważniejsze obszary struktury:

- `frontend/app/` — routing i layouty,
- `frontend/src/core/` — auth, api, env, theme i fundamenty techniczne,
- `frontend/src/features/` — logika funkcjonalna i moduły domenowe,
- `frontend/src/api/` — kontrakty i klienty generowane,
- `frontend/src/ui/` — współdzielone komponenty UI.

## Zasady obowiązkowe

- ZAWSZE odpowiadaj po polsku.
- ZAWSZE pisz docstringi po polsku.
- Najpierw wskaż pliki związane z problemem.
- Nie proponuj rozwiązań web-only, jeśli nie są zgodne z Expo / React Native.
- Nie zakładaj DOM-only API, jeśli nie ma potwierdzenia, że dany fragment działa na webie.

## Stan i dane

- TanStack Query służy do server state.
- Zustand służy tylko do local/app state.
- Nie przenoś odpowiedzialności za fetchowanie danych z backendu do losowych store'ów.
- Query keys powinny być spójne i przewidywalne.
- Inwalidację i cache projektuj świadomie.
- Nie ustawiaj długiego cache bez uzasadnienia biznesowego.

## Warstwy odpowiedzialności

- Routing zostaw w `frontend/app/`.
- Logikę domenową trzymaj w `frontend/src/features/`.
- Wspólne fundamenty techniczne trzymaj w `frontend/src/core/`.
- Wspólne UI trzymaj poza logiką biznesową.
- Nie wywołuj API bezpośrednio w dużych komponentach ekranowych, jeśli można użyć hooka, modułu api albo warstwy feature.

## Formularze i walidacja

- Preferuj `react-hook-form`.
- Walidację projektuj czytelnie, najlepiej z wykorzystaniem Zod, jeśli pasuje do istniejącego wzorca.
- Nie rozrzucaj walidacji po wielu warstwach bez potrzeby.

## Performance i DX

- Preferuj `async/await`.
- Używaj debounce przy wyszukiwaniu, filtrowaniu i wejściach generujących nadmiarowe requesty.
- Używaj lazy loading tam, gdzie ogranicza koszt ciężkich ekranów lub zależności.
- Uważaj na zbędne re-rendery, niestabilne callbacki i niepotrzebne memo.
- Nie dodawaj `useMemo` i `useCallback` bez wyraźnego powodu.

## Oczekiwany styl odpowiedzi

1. Krótka diagnoza.
2. Powiązane pliki frontendowe.
3. Problemy i ryzyka.
4. Plan zmian.
5. Jeśli ma sens: propozycja implementacji.
6. Czego nie udało się potwierdzić.
