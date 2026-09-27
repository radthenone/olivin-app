"""Wybór promocji dla pozycji koszyka i zamówienia (ADR 0022, 0023)."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from django.db.models import Count, F, Q, QuerySet

from apps.accounts.services.membership_service import is_premium
from apps.categories.models import Category
from apps.collections.models import Collection
from apps.orders.models import CartItem, OrderStatus
from apps.products.pricing import cost_floor
from apps.promotions.models import Promotion, PromotionKind
from common.money import Money

if TYPE_CHECKING:
    from apps.accounts.models import Customer

USED = "used_count"
USED_BY_CUSTOMER = "used_by_customer_count"


@dataclass(frozen=True, slots=True)
class AppliedPromotion:
    """Promocja wybrana dla pozycji i obniżka, którą na niej daje."""

    promotion: Promotion
    amount: Money


def best_promotions(
    items: Iterable[CartItem],
    *,
    user: Customer = None,
    email: str = "",
    code_promotion: Promotion | None = None,
) -> dict[Any, AppliedPromotion]:
    """Najkorzystniejsza promocja dla każdej pozycji — klucz to `item.pk`.

    Na pozycję działa najwyżej jedna promocja (ADR 0023). Obniżka dotyczy
    samego towaru, bez grawerunku, i jest przycinana do kosztu wariantu
    (ADR 0022) **przed** porównaniem — wygrywa to, co klient faktycznie
    dostaje, a nie większy nominał. Pozycja, której kosztu nie da się
    policzyć (brak aktywnego kursu kruszcu), nie dostaje żadnej promocji:
    bez progu nie ma gwarancji, że cena nie spadnie poniżej kosztu.

    Gość bez adresu (podgląd koszyka) nie ma sprawdzanego limitu na klienta —
    sprawdza go dopiero złożenie zamówienia, kiedy adres już jest.
    """
    rows = list(items)
    if not rows:
        return {}
    currency = rows[0].unit_price.currency
    subtotal = sum((item.line_total for item in rows), start=Money.zero(currency))

    candidates = [
        promotion
        for promotion in eligible_promotions(
            user=user, email=email, code_promotion=code_promotion
        )
        if _meets_cart_conditions(promotion, subtotal)
    ]
    if not candidates:
        return {}

    covers = _scope_checker(candidates, rows)
    result: dict[Any, AppliedPromotion] = {}
    for item in rows:
        applied = _best_for(item, [p for p in candidates if covers(p, item)])
        if applied is not None:
            result[item.pk] = applied
    return result


def eligible_promotions(
    *,
    user: Customer = None,
    email: str = "",
    code_promotion: Promotion | None = None,
) -> QuerySet[Promotion]:
    """Promocje w okresie, bez wyczerpanego limitu, dostępne dla tego klienta.

    Promocja z kodem przechodzi tylko wtedy, gdy to ją aktywował koszyk.
    Promocja z warunkiem członkostwa przechodzi tylko dla klienta premium
    (`CONTEXT.md`, Membership; ADR 0023).
    """
    codes = Q(code="")
    if code_promotion is not None:
        codes |= Q(pk=code_promotion.pk)

    membership = Q(requires_premium=False)
    if is_premium(user):
        membership |= Q(requires_premium=True)

    # Zamówienie anulowane oddaje użycie — klient nic nie kupił.
    live = ~Q(redemptions__order__status=OrderStatus.CANCELLED)
    promotions = (
        Promotion.objects.active()
        .filter(codes)
        .filter(membership)
        .annotate(**{USED: Count("redemptions", filter=live)})
        .filter(Q(global_limit__isnull=True) | Q(global_limit__gt=F(USED)))
    )

    customer = _customer_filter(user=user, email=email)
    if customer is not None:
        promotions = promotions.annotate(
            **{USED_BY_CUSTOMER: Count("redemptions", filter=live & customer)}
        ).filter(
            Q(per_customer_limit__isnull=True)
            | Q(per_customer_limit__gt=F(USED_BY_CUSTOMER))
        )
    return promotions.prefetch_related("products", "collections", "categories")


def _customer_filter(*, user: Customer, email: str) -> Q | None:
    """Zamówienia tego samego klienta: konta albo — dla gościa — adresu."""
    if user is not None:
        return Q(redemptions__order__user=user) | Q(
            redemptions__order__email__iexact=user.email
        )
    if email:
        return Q(redemptions__order__email__iexact=email)
    return None


def _meets_cart_conditions(promotion: Promotion, subtotal: Money) -> bool:
    """Waluta i minimalna wartość koszyka — liczone przed rabatami."""
    uses_currency = (
        promotion.kind == PromotionKind.AMOUNT or promotion.min_cart_value is not None
    )
    if uses_currency and promotion.currency != subtotal.currency:
        return False
    minimum = promotion.min_cart_money
    return minimum is None or subtotal >= minimum


def _scope_checker(
    promotions: list[Promotion], rows: list[CartItem]
) -> Callable[[Promotion, CartItem], bool]:
    """Funkcja „czy promocja obejmuje pozycję" z zakresem wczytanym raz.

    Kategorie schodzą w dół drzewa: promocja na węzeł obejmuje produkty
    z każdego jego potomka, bo produkt siedzi w liściu (`Category.subtree_ids`).
    """
    parent_of = dict(Category.objects.values_list("id", "parent_id"))
    product_ids = {item.variant.product_id for item in rows}  # type: ignore[missing-attribute]
    collections_of: dict[Any, set[Any]] = {}
    through = Collection.products.through
    for product_id, collection_id in through.objects.filter(
        product_id__in=product_ids
    ).values_list("product_id", "collection_id"):
        collections_of.setdefault(product_id, set()).add(collection_id)

    scope = {
        promotion.pk: (
            {p.pk for p in promotion.products.all()},
            {c.pk for c in promotion.collections.all()},
            {c.pk for c in promotion.categories.all()},
        )
        for promotion in promotions
    }

    def ancestors(category_id: Any) -> set[Any]:
        chain: set[Any] = set()
        while category_id is not None and category_id not in chain:
            chain.add(category_id)
            category_id = parent_of.get(category_id)
        return chain

    def covers(promotion: Promotion, item: CartItem) -> bool:
        if promotion.whole_catalog:
            return True
        products, collections, categories = scope[promotion.pk]
        product = item.variant.product
        return (
            product.pk in products
            or bool(collections & collections_of.get(product.pk, set()))
            or bool(categories & ancestors(product.category_id))  # type: ignore[missing-attribute]
        )

    return covers


def _best_for(item: CartItem, promotions: list[Promotion]) -> AppliedPromotion | None:
    if not promotions:
        return None
    headroom = _headroom(item)
    if headroom is None or headroom.amount <= 0:
        return None

    best: AppliedPromotion | None = None
    for promotion in promotions:
        amount = min(_nominal(promotion, item), headroom)
        if amount.amount <= 0:
            continue
        if best is None or amount > best.amount:
            best = AppliedPromotion(promotion=promotion, amount=amount)
    return best


def _headroom(item: CartItem) -> Money | None:
    """Ile towaru pozycji wolno obniżyć: cena minus koszt wariantu (ADR 0022)."""
    # ponytail: koszt liczony per pozycja (kurs + składniki = 2 zapytania);
    # przy koszykach po kilkadziesiąt pozycji wczytać kursy hurtem.
    floor = cost_floor(item.variant)
    goods = item.goods_price
    if floor is None or floor.currency != goods.currency:
        return None
    return goods - floor * (item.specimen_count * item.quantity)


def _nominal(promotion: Promotion, item: CartItem) -> Money:
    """Obniżka przed przycięciem: procent od towaru albo kwota na egzemplarz."""
    goods = item.goods_price
    if promotion.kind == PromotionKind.PERCENT:
        return goods.multiply(Decimal(promotion.value) / Decimal(100))
    return Money(promotion.value, goods.currency) * (
        item.specimen_count * item.quantity
    )
