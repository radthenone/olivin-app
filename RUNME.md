# Szybki Start

Ten plik jest krótką ściągą. Pełniejszy opis znajduje się w `README.md`.

## Instalacja zależności

```bash
cp .env.example .env
task packages:backend:sync
task packages:frontend:sync
```

## Backend

```bash
task backend:build
task db:migrate
task backend:logs
```

Linki w mailach (reset hasła, newsletter, koszyk) backend składa z jednej
zmiennej `FRONTEND_URL` (ADR 0038). Wpisz ją w `.envs/{dev,prod}/backend/django.env`,
np. `FRONTEND_URL=http://localhost:3000`. Na dev jest to wartość domyślna,
a w produkcji zmienna jest wymagana. Dawne `NEWSLETTER_CONFIRM_URL`,
`NEWSLETTER_UNSUBSCRIBE_URL`, `CART_URL` i `NOTIFICATION_PREFERENCES_URL`
nie są już czytane. Expo web (`:8081`) nie ma domyślnego originu w CORS/CSRF.
Gdy go używasz, dopisz go do `FRONTEND_URLS` i `CSRF_TRUSTED_ORIGINS`.

Nagłówek `List-Unsubscribe` (wypis jednym kliknięciem, RFC 8058) w mailach
marketingowych wskazuje API, więc backend potrzebuje też `BACKEND_URL` —
publicznego adresu HTTPS API (na dev domyślnie `http://localhost:8000`,
w produkcji wymagane).

## Frontend

```bash
task mobile:run
```

Wyczyść cache Metro:

```bash
task mobile:run:clear
```

## Android

```bash
task emulator:run -- S23
task mobile:run -- emulator-5554
```

## Kontrole

```bash
task test:backend-local -- src/ -m "not integration"
task lints:backend:ruff:check
task lints:backend:typecheck
task lints:frontend:lint
task lints:frontend:typecheck
```

Testy jednostkowe nie czytają `.env` ani `.envs/dev/*` (`DJANGO_ENVIRONMENT=testing`), więc nie potrzebują uruchomionego compose. Na Windowsie render PDF (WeasyPrint) wymaga bibliotek GTK — bez nich testy dokumentów padają z `OSError: cannot load library 'libgobject-2.0-0'`.
