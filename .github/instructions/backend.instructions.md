---
applyTo: "backend/**"
---

# Backend instructions — olivin-app

## Zakres

Te instrukcje dotyczą zmian w `backend/**`.

## Kontekst technologiczny

Backend to Django + Django REST Framework.
Najważniejsze obszary struktury:

- `backend/src/core/` — settings, urls, celery, envs, storage,
- `backend/src/apps/` — aplikacje domenowe,
- `backend/src/common/` — współdzielone elementy i abstrakcje,

## Zasady obowiązkowe

- ZAWSZE odpowiadaj po polsku.
- ZAWSZE pisz docstringi po polsku.
- Najpierw wskaż pliki związane z problemem.
- Nie zakładaj dodatkowych warstw, jeśli repo ich nie potwierdza.
- Nie rozlewaj logiki biznesowej po wielu warstwach bez wyraźnej potrzeby.

## Architektura i odpowiedzialności

- Widoki i viewsety powinny być cienkie.
- Logika biznesowa nie powinna siedzieć jednocześnie w modelu, serializerze i widoku.
- Walidację, permissions i bezpieczeństwo traktuj jako obowiązkowy element rozwiązania.
- Zwracaj uwagę na atomowość operacji i side effecty.
- Jeśli zadanie jest domenowe, umieszczaj je w odpowiedniej appce w `backend/src/apps/`.

## ORM i wydajność

- Oceń ryzyko N+1 queries.
- Rozważ `select_related` i `prefetch_related`, jeśli mają uzasadnienie.
- Nie optymalizuj na ślepo; najpierw wskaż realny problem.
- Dbaj o czytelność zapytań i ich testowalność.

## API i kontrakt

- Jeśli zmieniasz endpoint, serializer lub strukturę odpowiedzi, oceń wpływ na kontrakt API.
- Uwzględnij wpływ na `backend/src/schema.yaml`.
- Uwzględnij wpływ na frontend i generowane klienty lub typy.

## Oczekiwany styl odpowiedzi

1. Krótka diagnoza.
2. Powiązane pliki backendowe.
3. Problemy i ryzyka.
4. Plan zmian.
5. Jeśli ma sens: propozycja implementacji.
6. Czego nie udało się potwierdzić.
