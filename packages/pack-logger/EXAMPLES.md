# Pack Logger - Przykłady Kodu

Gotowe do skopiowania przykłady konfiguracji i użycia.

---

## 🔧 Backend - Konfiguracja

### `backend/pyproject.toml` - Dodaj dependency:

```toml
dependencies = [
    # ... existing dependencies ...
    "pack-logger @ file:///../packages/pack-logger/backend",
]
```

### `backend/src/core/settings/base.py` - Dodaj logging:

```python
from pack_logger import configure_logging

# ... existing code ...

# Konfiguracja logowania
LOGGING = configure_logging(debug=DEBUG, app_name='olivin')
```

### `backend/src/core/settings/components/middleware.py` - Dodaj middleware:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'pack_logger.middleware.ApiLoggingMiddleware',  # ← Dodaj tutaj
    'django.contrib.sessions.middleware.SessionMiddleware',
    # ... rest of middleware ...
]
```

---

## 🔧 Frontend - Konfiguracja

### `frontend/package.json` - Dodaj dependency:

```json
{
  "dependencies": {
    "@pack/logger": "file:../packages/pack-logger/frontend",
    // ... existing dependencies ...
  }
}
```

### `frontend/api/client.ts` - Pełna konfiguracja z loggingiem:

```typescript
import { API_CONFIG } from "@config/api";
import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from "axios";
import { log } from "@pack/logger";

const requestTimings = new Map<string, number>();

const apiClient = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

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

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const requestId = `${Date.now()}-${Math.random()}`;
    config.headers["X-Request-ID"] = requestId;
    requestTimings.set(requestId, Date.now());

    const logData: any = {};
    if (config.headers) {
      const usefulHeaders: Record<string, string> = {};
      ["content-type", "authorization", "accept", "user-agent"].forEach((key) => {
        const value = config.headers[key];
        if (value) usefulHeaders[key] = String(value);
      });
      Object.keys(config.headers).forEach((key) => {
        if (key.toLowerCase().startsWith("x-")) {
          usefulHeaders[key] = String(config.headers[key]);
        }
      });
      if (Object.keys(usefulHeaders).length > 0) logData.headers = usefulHeaders;
    }
    if (config.params) logData.queryParams = config.params;
    if (config.data) logData.body = maskSensitive(config.data);
    if (config.headers["content-type"]) logData.contentType = String(config.headers["content-type"]);

    log.apiRequest(config.method?.toUpperCase() || "GET", config.url || "", logData);
    return config;
  },
  (error: AxiosError) => {
    log.apiError("UNKNOWN", "Request setup failed", error);
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    const requestId = response.config.headers["X-Request-ID"] as string;
    const startTime = requestTimings.get(requestId);
    const duration = startTime ? Date.now() - startTime : 0;
    requestTimings.delete(requestId);

    const logData: any = {};
    if (response.headers) {
      const usefulHeaders: Record<string, string> = {};
      ["content-type", "content-length", "cache-control"].forEach((key) => {
        const value = response.headers[key];
        if (value) usefulHeaders[key] = String(value);
      });
      if (Object.keys(usefulHeaders).length > 0) logData.headers = usefulHeaders;
    }
    if (response.data) logData.body = response.data;

    log.apiResponse(
      response.config.method?.toUpperCase() || "GET",
      response.config.url || "",
      response.status,
      duration,
      logData
    );
    return response;
  },
  (error: AxiosError) => {
    const requestId = error.config?.headers?.["X-Request-ID"] as string;
    const startTime = requestTimings.get(requestId);
    const duration = startTime ? Date.now() - startTime : undefined;
    requestTimings.delete(requestId);

    const logData: any = {};
    if (error.response?.headers) {
      const usefulHeaders: Record<string, string> = {};
      ["content-type"].forEach((key) => {
        const value = error.response?.headers[key];
        if (value) usefulHeaders[key] = String(value);
      });
      if (Object.keys(usefulHeaders).length > 0) logData.headers = usefulHeaders;
    }

    log.apiError(
      error.config?.method?.toUpperCase() || "UNKNOWN",
      error.config?.url || "unknown",
      error,
      duration,
      logData
    );
    return Promise.reject(error);
  }
);

export default apiClient;
```

---

## 💻 Przykłady Użycia w Kodzie

### Backend - View Example

```python
# apps/orders/views.py
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from pack_logger import log
from .models import Order
from .serializers import OrderSerializer

class OrderViewSet(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def create(self, request, *args, **kwargs):
        log.info("Creating order", user_id=request.user.id)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = serializer.save(user=request.user)

        log.success("Order created",
                   order_id=order.id,
                   total=order.total,
                   items_count=order.items.count())

        return Response(serializer.data, status=201)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()

        log.warning("Cancelling order",
                   order_id=order.id,
                   user_id=request.user.id)

        order.status = 'cancelled'
        order.save()

        log.success("Order cancelled", order_id=order.id)
        return Response({'status': 'cancelled'})
```

### Backend - Service Example

```python
# apps/payments/services.py
from pack_logger import log
import stripe

class PaymentService:
    @staticmethod
    def process_payment(order_id: int, amount: float, token: str):
        log.info("Processing payment",
                order_id=order_id,
                amount=amount)

        try:
            charge = stripe.Charge.create(
                amount=int(amount * 100),
                currency='pln',
                source=token,
                description=f'Order #{order_id}'
            )

            log.success("Payment processed",
                       order_id=order_id,
                       transaction_id=charge.id,
                       amount=amount)

            return charge

        except stripe.error.CardError as e:
            log.error("Payment card error",
                     order_id=order_id,
                     error=str(e))
            raise

        except Exception as e:
            log.error("Payment processing failed",
                     order_id=order_id,
                     error=str(e),
                     error_type=type(e).__name__)
            raise
```

### Frontend - Component Example

```typescript
// app/products/[productId].tsx
import { useEffect, useState } from "react";
import { useLocalSearchParams } from "expo-router";
import { log } from "@pack/logger";
import apiClient from "@api/client";

export default function ProductDetailScreen() {
  const { productId } = useLocalSearchParams();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    log.info("Product detail screen opened", { productId });
    loadProduct();
  }, [productId]);

  const loadProduct = async () => {
    log.debug("Loading product details", { productId });
    setLoading(true);

    try {
      const response = await apiClient.get(`/api/products/${productId}/`);
      setProduct(response.data);

      log.success("Product loaded", {
        productId,
        name: response.data.name
      });
    } catch (error) {
      log.error("Failed to load product", { productId, error });
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async () => {
    log.info("Adding product to cart", { productId });

    try {
      await apiClient.post("/api/cart/items/", {
        product_id: productId,
        quantity: 1,
      });

      log.success("Product added to cart", { productId });
    } catch (error) {
      log.error("Failed to add product to cart", { productId, error });
    }
  };

  // ... render UI
}
```

### Frontend - Service Example

```typescript
// modules/orders/services/ordersApi.ts
import { log } from "@pack/logger";
import apiClient from "@api/client";

export interface Order {
  id: number;
  status: string;
  total: number;
  items: OrderItem[];
}

export class OrdersService {
  static async createOrder(orderData: {
    items: Array<{ product_id: number; quantity: number }>;
    shipping_address: any;
  }): Promise<Order> {
    log.info("Creating order", {
      itemsCount: orderData.items.length
    });

    try {
      const response = await apiClient.post<Order>("/api/orders/", orderData);

      log.success("Order created", {
        orderId: response.data.id,
        total: response.data.total
      });

      return response.data;
    } catch (error: any) {
      log.error("Order creation failed", {
        error: error.message,
        itemsCount: orderData.items.length
      });
      throw error;
    }
  }

  static async getOrder(orderId: string): Promise<Order> {
    log.debug("Fetching order", { orderId });

    try {
      const response = await apiClient.get<Order>(`/api/orders/${orderId}/`);
      return response.data;
    } catch (error: any) {
      log.error("Failed to fetch order", {
        orderId,
        error: error.message
      });
      throw error;
    }
  }

  static async cancelOrder(orderId: string): Promise<void> {
    log.warning("Cancelling order", { orderId });

    try {
      await apiClient.post(`/api/orders/${orderId}/cancel/`);
      log.success("Order cancelled", { orderId });
    } catch (error: any) {
      log.error("Failed to cancel order", {
        orderId,
        error: error.message
      });
      throw error;
    }
  }
}
```

---

## 📊 Przykładowe Outputy Logów

### Backend Console Output:

```
2024-01-15 10:30:15.123 INFO     API Request: POST /api/orders/
{
  "method": "POST",
  "path": "/api/orders/",
  "user": "john.doe@example.com",
  "user_id": 123,
  "ip": "127.0.0.1",
  "headers": {
    "content-type": "application/json",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
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
      "city": "Warsaw",
      "postal_code": "00-001"
    }
  },
  "content_type": "application/json"
}

2024-01-15 10:30:15.168 INFO     Order created
{
  "order_id": 789,
  "total": 299.99,
  "items_count": 3
}

2024-01-15 10:30:15.169 INFO     API Response: POST /api/orders/ [201] 45.23ms
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
    "created_at": "2024-01-15T10:30:15.123Z"
  }
}
```

### Frontend Console Output (Browser DevTools):

```
[10:30:15.123] [pack] API Request: POST /api/orders/
Data:
  headers: {
    "content-type": "application/json",
    "accept": "application/json"
  }
  body: {
    "items": [
      {"product_id": 1, "quantity": 2},
      {"product_id": 5, "quantity": 1}
    ],
    "shipping_address": {
      "street": "Main St 123",
      "city": "Warsaw"
    }
  }
  contentType: "application/json"

[10:30:15.456] [pack] API Response: POST /api/orders/ [201] 333ms
Data:
  status: 200
  duration: "333ms"
  headers: {
    "content-type": "application/json",
    "content-length": "256"
  }
  body: {
    "id": 789,
    "status": "pending",
    "total": 299.99,
    "createdAt": "2024-01-15T10:30:15.123Z"
  }

[10:30:20.789] [pack] Order created
Data:
  orderId: 789
  total: 299.99
  itemsCount: 3
```

---

## 🎨 Kolory w Konsoli

### Backend (Rich):
- **INFO**: Cyan
- **WARNING**: Yellow
- **ERROR**: Red Bold
- **SUCCESS**: Green Bold

### Frontend (Browser):
- **DEBUG**: Gray (#6B7280)
- **INFO**: Blue (#3B82F6)
- **WARN**: Orange (#F59E0B)
- **ERROR**: Red (#EF4444)
- **SUCCESS**: Green (#10B981)

---

Gotowe! Skopiuj odpowiednie fragmenty do swojego projektu. 🚀

