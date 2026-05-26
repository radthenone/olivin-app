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

## Frontend

```bash
task frontend:run
```

Wyczyść cache Metro:

```bash
task frontend:run:clear
```

## Android

```bash
task emulator:run -- S23
task frontend:run -- emulator-5554
```

## Kontrole

```bash
task test:backend-local -- src/ -m "not integration"
task lints:backend:ruff:check
task lints:backend:typecheck
task lints:frontend:lint
task lints:frontend:typecheck
```
