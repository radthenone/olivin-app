# Pack Logger - Przewodnik Użycia

Kompletny przewodnik instalacji, konfiguracji i użycia loggera w aplikacji Olivin.

---

## 📦 Instalacja

### Backend (Django)

#### 1. Dodaj paczkę do `backend/pyproject.toml`:

```toml
dependencies = [
    # ... existing dependencies ...
    "pack-logger @ file:///../packages/pack-logger/backend",
]
```

#### 2. Zainstaluj paczkę:

```bash
cd backend
uv sync
```

### Frontend (React Native/Expo)

#### 1. Dodaj paczkę do `frontend/package.json`:

```json
{
    "dependencies": {
        "@pack/logger": "file:../packages/pack-logger/frontend"
        // ... existing dependencies ...
    }
}
```

#### 2. Zbuduj paczkę TypeScript (pierwszorazowo):

```bash
cd packages/pack-logger/frontend
npm install
npm run build
```

#### 3. Zainstaluj w projekcie:

```bash
cd frontend
npm install
```

---

## ⚙️ Konfiguracja

### Backend - Django Settings

#### 1. Zaktualizuj `backend/src/core/settings/base.py`:

```python
"""
Base Django settings for Olivin project.
"""
import os
from datetime import timedelta
from core.paths import SRC_DIR, BASE_DIR, PROJECT_DIR, load_valid_envs
from pack_logger import configure_logging  # ← Dodaj import

load_valid_envs()

# ... existing code ...

# Konfiguracja logowania
LOGGING = configure_logging(debug=DEBUG, app_name='olivin')
```

#### 2. Dodaj middleware do `backend/src/core/settings/components/middleware.py`:

```python
"""
Django middleware configuration.
"""
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'pack_logger.middleware.ApiLoggingMiddleware',  # ← Dodaj tutaj (przed CamelCaseMiddleWare)
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "allauth.account.middleware.AccountMiddleware",
    'djangorestframework_camel_case.middleware.CamelCaseMiddleWare',  # ← Case conversion
]
```

### Frontend - API Client

Zaktualizuj `frontend/api/client.ts`:

```typescript
import { API_CONFIG } from "@config/api";
import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from "axios";
import { log } from "@pack/logger";

/**
 * Tracking czasu requestów
 */
const requestTimings = new Map<string, number>();

/**
 * API Client
 */
const apiClient = axios.create({
    baseURL: API_CONFIG.BASE_URL,
    timeout: 10000,
    headers: {
        "Content-Type": "application/json",
    },
});

/**
 * Maskuje wrażliwe dane
 */
const maskSensitive = (data: any): any => {
    if (!data || typeof data !== "object") return data;

    const sensitive = ["password", "token", "secret", "apiKey", "cardNumber", "cvv"];
    const masked = Array.isArray(data) ? [...data] : { ...data };

    for (const key in masked) {
        if (sensitive.some((s) => key.toLowerCase().includes(s.toLowerCase()))) {
            masked[key] = "***";
        } else if (typeof masked[key] === "object") {
            masked[key] = maskSensitive(masked[key]);
        }
    }

    return masked;
};

/**
 * Request Interceptor - loguje z pełnymi danymi
 */
apiClient.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        const requestId = `${Date.now()}-${Math.random()}`;
        config.headers["X-Request-ID"] = requestId;
        requestTimings.set(requestId, Date.now());

        // Przygotuj dane do logowania
        const logData: any = {};

        // Headers (wybrane, przydatne)
        if (config.headers) {
            const usefulHeaders: Record<string, string> = {};
            const headerKeys = ["content-type", "authorization", "accept", "user-agent"];

            headerKeys.forEach((key) => {
                const value = config.headers[key];
                if (value) {
                    usefulHeaders[key] = String(value);
                }
            });

            // Dodaj wszystkie custom headers (X-*)
            Object.keys(config.headers).forEach((key) => {
                if (key.toLowerCase().startsWith("x-")) {
                    usefulHeaders[key] = String(config.headers[key]);
                }
            });

            if (Object.keys(usefulHeaders).length > 0) {
                logData.headers = usefulHeaders;
            }
        }

        // Query params
        if (config.params) {
            logData.queryParams = config.params;
        }

        // Body (camelCase - frontend standard)
        if (config.data) {
            logData.body = maskSensitive(config.data);
        }

        if (config.headers["content-type"]) {
            logData.contentType = String(config.headers["content-type"]);
        }

        // Loguj request
        log.apiRequest(config.method?.toUpperCase() || "GET", config.url || "", logData);

        return config;
    },
    (error: AxiosError) => {
        log.apiError("UNKNOWN", "Request setup failed", error);
        return Promise.reject(error);
    }
);

/**
 * Response Interceptor - loguje z pełnymi danymi
 */
apiClient.interceptors.response.use(
    (response: AxiosResponse) => {
        const requestId = response.config.headers["X-Request-ID"] as string;
        const startTime = requestTimings.get(requestId);
        const duration = startTime ? Date.now() - startTime : 0;

        requestTimings.delete(requestId);

        // Przygotuj dane do logowania
        const logData: any = {};

        // Headers (wybrane)
        if (response.headers) {
            const usefulHeaders: Record<string, string> = {};
            const headerKeys = ["content-type", "content-length", "cache-control"];

            headerKeys.forEach((key) => {
                const value = response.headers[key];
                if (value) {
                    usefulHeaders[key] = String(value);
                }
            });

            if (Object.keys(usefulHeaders).length > 0) {
                logData.headers = usefulHeaders;
            }
        }

        // Body (już w camelCase dzięki backend renderer)
        if (response.data) {
            logData.body = response.data;
        }

        // Loguj response
        log.apiResponse(response.config.method?.toUpperCase() || "GET", response.config.url || "", response.status, duration, logData);

        return response;
    },
    (error: AxiosError) => {
        const requestId = error.config?.headers?.["X-Request-ID"] as string;
        const startTime = requestTimings.get(requestId);
        const duration = startTime ? Date.now() - startTime : undefined;

        requestTimings.delete(requestId);

        // Przygotuj dane do logowania
        const logData: any = {};

        if (error.response?.headers) {
            const usefulHeaders: Record<string, string> = {};
            const headerKeys = ["content-type"];

            headerKeys.forEach((key) => {
                const value = error.response?.headers[key];
                if (value) {
                    usefulHeaders[key] = String(value);
                }
            });

            if (Object.keys(usefulHeaders).length > 0) {
                logData.headers = usefulHeaders;
            }
        }

        // Loguj error
        log.apiError(error.config?.method?.toUpperCase() || "UNKNOWN", error.config?.url || "unknown", error, duration, logData);

        return Promise.reject(error);
    }
);

export default apiClient;
```

---

## 💻 Użycie w Kodzie

### Backend - Przykłady

#### 1. Podstawowe użycie w views/services:

```python
from pack_logger import log

def create_order(request):
    """Tworzy nowe zamówienie."""
    log.info("Creating order", user_id=request.user.id, cart_items=5)

    try:
        order = Order.objects.create(
            user=request.user,
            total=100.00,
            status='pending'
        )

        log.success("Order created", order_id=order.id, total=order.total)
        return order

    except Exception as e:
        log.error("Order creation failed", error=str(e), user_id=request.user.id)
        raise


def get_products(request):
    """Pobiera listę produktów."""
    log.debug("Fetching products", category=request.GET.get('category'))

    products = Product.objects.all()

    log.info("Products fetched", count=products.count())
    return products
```

#### 2. Użycie w health check:

```python
from django.http import JsonResponse
from pack_logger import log

def health_check(request):
    """Health check endpoint."""
    log.debug("Health check called", endpoint="/api/health/")

    return JsonResponse({
        "status": "ok",
        "timestamp": timezone.now().isoformat()
    })
```

#### 3. Użycie w custom middleware/serwisach:

```python
from pack_logger import log

class PaymentService:
    def process_payment(self, order_id: int, amount: float):
        log.info("Processing payment", order_id=order_id, amount=amount)

        try:
            # Proces płatności
            result = stripe.charge(...)

            log.success("Payment processed",
                       order_id=order_id,
                       transaction_id=result.id)
            return result

        except Exception as e:
            log.error("Payment failed",
                     order_id=order_id,
                     error=str(e))
            raise
```

### Frontend - Przykłady

#### 1. Użycie w komponentach:

```typescript
import { log } from "@pack/logger";
import { useEffect, useState } from "react";
import apiClient from "@api/client";

export default function ProductsScreen() {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        log.info("Products screen mounted", { screen: "Products" });
    }, []);

    const loadProducts = async () => {
        log.info("Loading products", { category: "electronics", page: 1 });
        setLoading(true);

        try {
            const response = await apiClient.get("/api/products/", {
                params: { category: "electronics", page: 1 },
            });

            setProducts(response.data);
            log.success("Products loaded", { count: response.data.length });
        } catch (error) {
            log.error("Failed to load products", { error });
        } finally {
            setLoading(false);
        }
    };

    return <View>{/* UI */}</View>;
}
```

#### 2. Użycie w serwisach:

```typescript
import { log } from "@pack/logger";
import apiClient from "@api/client";

export class OrderService {
    static async createOrder(orderData: any) {
        log.info("Creating order", { itemsCount: orderData.items.length });

        try {
            const response = await apiClient.post("/api/orders/", orderData);

            log.success("Order created", { orderId: response.data.id });
            return response.data;
        } catch (error) {
            log.error("Order creation failed", { error });
            throw error;
        }
    }

    static async getOrder(orderId: string) {
        log.debug("Fetching order", { orderId });

        try {
            const response = await apiClient.get(`/api/orders/${orderId}/`);
            return response.data;
        } catch (error) {
            log.error("Failed to fetch order", { orderId, error });
            throw error;
        }
    }
}
```

---

## 📊 Przykładowe Logi

### Backend - Konsola (Rich)

#### Request Log:

```
API Request: POST /api/orders/
{
  "method": "POST",
  "path": "/api/orders/",
  "user": "john.doe@example.com",
  "user_id": 123,
  "ip": "127.0.0.1",
  "headers": {
    "content-type": "application/json",
    "user-agent": "Mozilla/5.0...",
    "accept": "application/json"
  },
  "query_params": null,
  "body": {
    "items": [
      {"product_id": 1, "quantity": 2},
      {"product_id": 5, "quantity": 1}
    ],
    "shipping_address": {
      "street": "Main St 123",
      "city": "Warsaw"
    }
  },
  "content_type": "application/json"
}
```

#### Response Log:

```
API Response: POST /api/orders/ [201] 45.23ms
{
  "method": "POST",
  "path": "/api/orders/",
  "status": 201,
  "duration_ms": 45.23,
  "headers": {
    "content-type": "application/json",
    "content-length": "256"
  },
  "body": {
    "id": 789,
    "status": "pending",
    "total": 299.99,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

#### Custom Log:

```
User logged in
{
  "user_id": 123,
  "email": "john.doe@example.com",
  "ip": "127.0.0.1"
}
```

### Frontend - Konsola (Browser/React Native)

#### Request Log:

```
[10:30:15.123] [pack] API Request: GET /api/products/
Data:
  headers: {
    "content-type": "application/json",
    "accept": "application/json"
  }
  queryParams: {
    "category": "electronics",
    "page": 1
  }
  contentType: "application/json"
```

#### Response Log:

```
[10:30:15.456] [pack] API Response: GET /api/products/ [200] 333ms
Data:
  status: 200
  duration: "333ms"
  headers: {
    "content-type": "application/json",
    "content-length": "2048"
  }
  body: {
    "count": 25,
    "results": [
      {"id": 1, "name": "Laptop", "price": 999.99},
      {"id": 2, "name": "Phone", "price": 599.99},
      ...
    ]
  }
```

#### Custom Log:

```
[10:30:20.789] [pack] Products loaded
Data:
  count: 25
  category: "electronics"
```

#### Error Log:

```
[10:30:25.012] [pack] API Error: POST /api/orders/ FAILED
Data:
  error: "Network Error"
  status: undefined
  duration: "5000ms"
  responseData: {
    "error": "Request timeout"
  }
```

---

## 🎯 Funkcje Loggera

### Backend (Python)

```python
from pack_logger import log

# Podstawowe logi
log.debug("Debug message", key="value")
log.info("Info message", key="value")
log.warning("Warning message", key="value")
log.error("Error message", key="value")
log.success("Success message", key="value")

# API logging (automatycznie przez middleware)
# Lub ręcznie:
log.api_request(
    method="POST",
    path="/api/orders/",
    user="john@example.com",
    ip="127.0.0.1",
    headers={"content-type": "application/json"},
    query_params={"page": 1},
    body={"items": [...]},
    content_type="application/json"
)

log.api_response(
    method="POST",
    path="/api/orders/",
    status=201,
    duration_ms=45.23,
    headers={"content-type": "application/json"},
    body={"id": 789, "status": "pending"}
)
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

// API logging (automatycznie przez interceptors)
// Lub ręcznie:
log.apiRequest("POST", "/api/orders/", {
  headers: { "content-type": "application/json" },
  queryParams: { page: 1 },
  body: { items: [...] },
  contentType: "application/json",
});

log.apiResponse("POST", "/api/orders/", 201, 333, {
  headers: { "content-type": "application/json" },
  body: { id: 789, status: "pending" },
});

log.apiError("POST", "/api/orders/", error, 5000, {
  headers: { "content-type": "application/json" },
});
```

---

## 🔒 Bezpieczeństwo

Logger automatycznie maskuje wrażliwe dane:

-   **Headers**: `authorization`, `cookie`, `x-csrftoken`, `x-api-key`, `session`
-   **Body fields**: `password`, `token`, `secret`, `api_key`, `access_token`, `refresh_token`, `card_number`, `cvv`, `ssn`

Przykład:

```python
# Input:
{
  "email": "user@example.com",
  "password": "secret123",
  "card_number": "1234-5678-9012-3456"
}

# W logach:
{
  "email": "user@example.com",
  "password": "***MASKED***",
  "card_number": "***MASKED***"
}
```

---

## 📝 Uwagi

1. **Case Conversion**: Automatyczna konwersja `camelCase` ↔ `snake_case` działa dzięki:

    - Backend: `CamelCaseMiddleWare` i `CamelCaseJSONRenderer`
    - Frontend: Dane są już w `camelCase` (standard frontend)

2. **Performance**: Logger nie wpływa znacząco na wydajność - loguje asynchronicznie

3. **Development vs Production**:

    - W development: wszystkie logi są widoczne
    - W production: tylko błędy są logowane (można zmienić w konfiguracji)

4. **Excluded Paths**: Automatycznie pomijane:
    - `/admin/`
    - `/static/`
    - `/media/`
    - `/favicon.ico`
    - `/api/health/`

---
