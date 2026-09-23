"""
Ustawienia sklepu — pojedyncze liczby wspólne dla całego katalogu.

Trafiają tutaj, a nie do modelu konfiguracji, wartości spełniające trzy
warunki naraz: jest ich dokładnie po jednej, nie mają historii i nie różnią
się między wariantami sprzedaży. Model wymagałby wymuszenia jedynego wiersza,
migracji i ekranu w panelu dla jednej kwoty; zmienna środowiskowa zmienia się
bez wdrożenia nowego kodu. Wartość z wariantami (stawka metody dostawy,
promocja) to model, nie ustawienie.
"""

import os

# Próg darmowej dostawy wspólny dla sklepu (`CONTEXT.md`, ShippingMethod).
# Grosze; pusta wartość wyłącza darmową dostawę całkowicie.
_free_shipping_threshold = os.environ.get("FREE_SHIPPING_THRESHOLD", "50000").strip()
FREE_SHIPPING_THRESHOLD: int | None = (
    int(_free_shipping_threshold) if _free_shipping_threshold else None
)
