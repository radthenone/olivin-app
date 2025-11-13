# Pack Logger 📦

Uniwersalny system logowania dla aplikacji Olivin - Backend (Django) i Frontend (React Native/Expo).

## ✨ Features

-   🎨 **Kolorowe logi** - Rich w Pythonie, kolorowa konsola w TypeScript
-   📊 **Pełne dane developerskie** - Headers, params, query params, body
-   🔒 **Automatyczne maskowanie** - Wrażliwe dane (password, token, etc.) są automatycznie maskowane
-   🔄 **Case conversion** - Automatyczna konwersja camelCase ↔ snake_case
-   ⚡ **Wydajność** - Minimalny wpływ na performance aplikacji
-   🚫 **Bez plików** - Tylko konsola, bez zapisu do plików

## 🚀 Quick Start

### Backend

1. **Dodaj do `pyproject.toml`:**

```toml
dependencies = [
    "pack-logger @ file:///../packages/pack-logger/backend",
]
```

2. **Zainstaluj:**

```bash
cd backend
uv sync
```

3. **Skonfiguruj w `settings/base.py`:**

```python
from pack_logger import configure_logging

LOGGING = configure_logging(debug=DEBUG, app_name='olivin')
```

4. **Dodaj middleware w `settings/components/middleware.py`:**

```python
MIDDLEWARE = [
    'pack_logger.middleware.ApiLoggingMiddleware',  # ← Dodaj tutaj
    # ... rest
]
```

### Frontend

1. **Dodaj do `package.json`:**

```json
{
    "dependencies": {
        "@pack/logger": "file:../packages/pack-logger/frontend"
    }
}
```

2. **Zbuduj paczkę:**

```bash
cd packages/pack-logger/frontend
npm install && npm run build
```

3. **Zainstaluj:**

```bash
cd frontend
npm install
```

4. **Użyj w kodzie:**

```typescript
import { log } from "@pack/logger";

log.info("User logged in", { userId: 123 });
```

## 📖 Dokumentacja

-   **[USAGE.md](./USAGE.md)** - Kompletny przewodnik użycia
-   **[EXAMPLES.md](./EXAMPLES.md)** - Gotowe przykłady kodu

## 💻 Podstawowe Użycie

### Backend (Python)

```python
from pack_logger import log

# Podstawowe logi
log.debug("Debug message", key="value")
log.info("Info message", key="value")
log.warning("Warning message", key="value")
log.error("Error message", key="value")
log.success("Success message", key="value")
```

### Frontend (TypeScript)

```typescript
import { log } from "@pack/logger";

// Podstawowe logi
log.debug("Debug message", { key: "value" });
log.info("Info message", { key: "value" });
log.warn("Warning message", { key: "value" });
log.error("Error message", { key: "value" });
log.success("Success message", { key: "value" });
```

## 📊 Przykładowe Logi

### Backend Output:

```
API Request: POST /api/orders/
{
  "method": "POST",
  "path": "/api/orders/",
  "user": "john@example.com",
  "headers": {...},
  "body": {...}
}

API Response: POST /api/orders/ [201] 45.23ms
{
  "status": 201,
  "duration_ms": 45.23,
  "body": {...}
}
```

### Frontend Output:

```
[10:30:15.123] [pack] API Request: POST /api/orders/
Data:
  headers: {...}
  body: {...}

[10:30:15.456] [pack] API Response: POST /api/orders/ [201] 333ms
Data:
  status: 201
  body: {...}
```

## 🔒 Bezpieczeństwo

Automatyczne maskowanie wrażliwych danych:

-   Headers: `authorization`, `cookie`, `x-csrftoken`
-   Body: `password`, `token`, `secret`, `card_number`, `cvv`

## 📝 Uwagi

-   Middleware automatycznie loguje wszystkie API requesty/response
-   Case conversion działa automatycznie (camelCase ↔ snake_case)
-   W production tylko błędy są logowane (można zmienić w konfiguracji)

## 📚 Więcej Informacji

Zobacz [USAGE.md](./USAGE.md) dla pełnej dokumentacji i [EXAMPLES.md](./EXAMPLES.md) dla gotowych przykładów.

---
