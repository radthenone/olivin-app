from __future__ import annotations

import secrets
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import QuerySet

from apps.orders.models import MAX_ITEM_QUANTITY, Cart, CartItem
from apps.products.models import ProductVariant
from common.money import DEFAULT_CURRENCY, Money

# Token gościa ma być nie do odgadnięcia — jest jedynym kluczem do koszyka,
# który nie ma właściciela. 32 bajty losowości dają ~43 znaki w base64url.
GUEST_TOKEN_BYTES = 32


class CartError(ValidationError):
    """Odmowa zmiany w koszyku, którą klient ma zobaczyć jako 400."""


@dataclass(frozen=True, slots=True)
class CartTotals:
    """Podsumowanie koszyka policzone na backendzie.

    Rabat i kupon są tu od początku, choć dziś zawsze zerowe: kontrakt kasy
    ma nie zmieniać kształtu, gdy dojdą promocje (#153) i kupony (#154).
    Klient, który już rysuje te wiersze, nie będzie musiał ich dokładać.
    """

    item_count: int
    subtotal: Money
    discount_amount: Money
    coupon_amount: Money
    total: Money


def new_guest_token() -> str:
    return secrets.token_urlsafe(GUEST_TOKEN_BYTES)


def cart_items(cart: Cart) -> QuerySet[CartItem]:
    """Pozycje wraz z tym, czego potrzebuje wycena — bez dobijania bazy."""
    return cart.items.select_related(  # type: ignore[missing-attribute]
        "variant", "variant__product", "variant__inventory"
    ).order_by("created_at", "id")


def totals(cart: Cart) -> CartTotals:
    """Sumuje pozycje po cenie aktualnej (`CONTEXT.md`, CartItem)."""
    items = list(cart_items(cart))
    currency = items[0].unit_price.currency if items else DEFAULT_CURRENCY
    subtotal = sum((item.line_total for item in items), start=Money.zero(currency))
    zero = Money.zero(currency)
    return CartTotals(
        item_count=len(items),
        subtotal=subtotal,
        discount_amount=zero,
        coupon_amount=zero,
        total=subtotal,
    )


def get_cart(*, user=None, token: str | None = None) -> Cart | None:
    """Koszyk konta albo gościa; `None`, gdy żadnego jeszcze nie ma."""
    if user is not None and user.is_authenticated:
        return Cart.objects.filter(user=user).first()
    if token:
        return Cart.objects.guest().filter(session_key=token).first()
    return None


def get_or_create_cart(*, user=None, token: str | None = None) -> Cart:
    """Koszyk do zapisu — zakładany przy pierwszym dodaniu pozycji (ADR 0030).

    Gość dostaje tu swój token. Token nieznany backendowi nie jest błędem:
    koszyk mógł już wygasnąć albo zostać scalony z kontem, a klient ma wtedy
    zacząć od nowa, a nie zobaczyć 404 przy dodawaniu do koszyka.
    """
    existing = get_cart(user=user, token=token)
    if existing is not None:
        return existing
    if user is not None and user.is_authenticated:
        return Cart.objects.create(user=user)
    return Cart.objects.create(session_key=new_guest_token())


@transaction.atomic
def add_item(
    cart: Cart,
    *,
    variant: ProductVariant,
    quantity: int = 1,
    engraving_text: str = "",
    second_size: str = "",
    second_engraving_text: str = "",
) -> CartItem:
    """Dokłada pozycję albo dolicza sztuki do pozycji o tej samej personalizacji.

    Scalanie idzie po wariancie **i** parametrach personalizacji: ten sam
    wyrób z innym grawerunkiem to osobna pozycja (ADR 0018), więc sumowanie
    ilości po samym wariancie zlałoby dwa różne towary w jeden.
    """
    personalisation = {
        "engraving_text": engraving_text,
        "second_size": second_size,
        "second_engraving_text": second_engraving_text,
    }
    item = (
        CartItem.objects.select_for_update()
        .filter(cart=cart, variant=variant, **personalisation)
        .first()
    )
    wanted = quantity + (item.quantity if item is not None else 0)

    _reject_quantity_above_limit(wanted)
    _reject_quantity_above_stock(variant, wanted)

    if item is None:
        item = CartItem(cart=cart, variant=variant, quantity=wanted, **personalisation)
    else:
        item.quantity = wanted
    item.full_clean(exclude=["cart"])
    item.save()
    cart.touch()
    return item


@transaction.atomic
def set_quantity(item: CartItem, quantity: int) -> CartItem:
    """Ustawia liczbę sztuk pozycji; zero usuwa pozycję z koszyka."""
    if quantity <= 0:
        remove_item(item)
        return item

    _reject_quantity_above_limit(quantity)
    _reject_quantity_above_stock(item.variant, quantity)
    item.quantity = quantity
    item.save(update_fields=["quantity", "updated_at"])
    item.cart.touch()
    return item


@transaction.atomic
def remove_item(item: CartItem) -> None:
    cart = item.cart
    item.delete()
    cart.touch()


@transaction.atomic
def merge_carts(*, guest: Cart, target: Cart) -> Cart:
    """Przenosi pozycje gościa do koszyka konta i kasuje koszyk gościa.

    Jedyny moment, w którym dwa koszyki stają się jednym (ADR 0030). Pozycje
    o tej samej personalizacji sumują ilości — z zachowaniem limitu sztuk,
    bo scalenie nie jest furtką do ominięcia go. Pozostałe trafiają obok.
    Token gościa przestaje działać razem z jego koszykiem.
    """
    if guest.pk == target.pk:
        return target

    for item in cart_items(guest):
        existing = CartItem.objects.filter(
            cart=target,
            variant=item.variant,
            engraving_text=item.engraving_text,
            second_size=item.second_size,
            second_engraving_text=item.second_engraving_text,
        ).first()
        if existing is None:
            item.cart = target
            item.save(update_fields=["cart", "updated_at"])
            continue
        existing.quantity = min(existing.quantity + item.quantity, MAX_ITEM_QUANTITY)
        existing.save(update_fields=["quantity", "updated_at"])
        item.delete()

    guest.delete()
    target.touch()
    return target


def _reject_quantity_above_limit(quantity: int) -> None:
    if quantity > MAX_ITEM_QUANTITY:
        raise CartError(
            {
                "quantity": (
                    f"Najwyżej {MAX_ITEM_QUANTITY} sztuki tej samej pozycji "
                    "w jednym zamówieniu."
                )
            }
        )


def _reject_quantity_above_stock(variant: ProductVariant, quantity: int) -> None:
    """Produkt na zamówienie omija sprawdzenie — nie ma stanu (ADR 0024)."""
    available = variant.available
    if available is None:
        return
    if quantity > available:
        raise CartError(
            {
                "quantity": (
                    f"Na stanie jest {available} szt. tego wariantu, "
                    f"a w koszyku miałoby być {quantity}."
                )
            }
        )
