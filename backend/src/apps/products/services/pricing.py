from __future__ import annotations

from apps.products.models.variant import ProductVariant
from apps.products.pricing import calculate_price


def recalculate_prices(metal: str, fineness: str) -> int:
    """Przelicza `price` wariantów wykonanych z danego kruszcu i próby.

    `manual_price` nie jest dotykana: to świadoma decyzja właściciela
    o konkretnym wariancie i kurs kruszcu nie ma prawa jej nadpisać
    (ADR 0022).

    Zwraca liczbę wariantów, którym cena faktycznie się zmieniła — zapis bez
    zmiany wartości tylko przesuwałby `updated_at` i zaśmiecał dziennik.
    """
    variants = (
        ProductVariant.objects.filter(
            product__material=metal, product__fineness=fineness
        )
        .select_related("product", "product__category")
        .prefetch_related("cost_components")
    )

    changed = []
    for variant in variants:
        price = calculate_price(variant)
        if price is None or price.amount == variant.price:
            continue
        variant.price = price.amount
        changed.append(variant)

    if changed:
        ProductVariant.objects.bulk_update(changed, ["price", "updated_at"])
    return len(changed)
