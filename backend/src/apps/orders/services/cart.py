from __future__ import annotations

import secrets
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from apps.orders.models import MAX_ITEM_QUANTITY, Cart, CartItem
from apps.products.models import ProductVariant
from apps.promotions.models import Promotion, normalise_code
from apps.promotions.services import AppliedPromotion, best_promotions
from common.money import DEFAULT_CURRENCY, Money

if TYPE_CHECKING:
    from apps.accounts.models import Customer

# Token gościa ma być nie do odgadnięcia — jest jedynym kluczem do koszyka,
# który nie ma właściciela. 32 bajty losowości dają ~43 znaki w base64url.
GUEST_TOKEN_BYTES = 32


class CartError(ValidationError):
    """Odmowa zmiany w koszyku, którą klient ma zobaczyć jako 400."""


@dataclass(frozen=True, slots=True)
class Personalisation:
    """Cechy, które odróżniają dwie pozycje na ten sam wariant (ADR 0018, 0024).

    Osobny typ, bo te trzy pola chodzą razem przez serializer, serwis i model,
    a każde miejsce, które rozpisuje je z osobna, prędzej czy później pominie
    jedno z nich i zleje dwa różne towary w jedną pozycję.
    """

    engraving_text: str = ""
    second_size: str = ""
    second_engraving_text: str = ""

    @classmethod
    def of(cls, item: CartItem) -> Personalisation:
        return cls(
            engraving_text=item.engraving_text,
            second_size=item.second_size,
            second_engraving_text=item.second_engraving_text,
        )

    def as_fields(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CartTotals:
    """Podsumowanie koszyka policzone na backendzie.

    Rabat to suma promocji na pozycjach (ADR 0023). Kupon jest tu od
    początku, choć dziś zawsze zerowy: kontrakt kasy ma nie zmieniać
    kształtu, gdy dojdą kupony (#154).
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
    return (
        cart.items.select_related(  # type: ignore[missing-attribute]
            "variant", "variant__product", "variant__inventory"
        )
        .prefetch_related("variant__cost_components")
        # Zdjęcia raz dla całego koszyka, a nie raz na wiersz: miniatura
        # w rozwijanej liście nie może kosztować zapytania na pozycję.
        .prefetch_related("variant__images", "variant__product__images")
        .order_by("created_at", "id")
    )


def totals(
    items: Iterable[CartItem],
    discounts: Mapping[Any, AppliedPromotion] | None = None,
) -> CartTotals:
    """Sumuje gotowe pozycje po cenie aktualnej (`CONTEXT.md`, CartItem).

    Bierze listę, a nie koszyk: widok i tak potrzebuje tych samych pozycji do
    odpowiedzi, a pobieranie ich drugi raz dawałoby dwa zapytania i dwie
    szanse na rozjazd między sumą a tym, co klient widzi. Rabaty przychodzą
    gotowe z `promotions_for` — ten sam wynik trafia potem do zamówienia.
    """
    rows = list(items)
    currency = rows[0].unit_price.currency if rows else DEFAULT_CURRENCY
    zero = Money.zero(currency)
    subtotal = sum((item.line_total for item in rows), start=zero)
    discount = sum(
        (applied.amount for applied in (discounts or {}).values()), start=zero
    )
    return CartTotals(
        item_count=len(rows),
        subtotal=subtotal,
        discount_amount=discount,
        coupon_amount=zero,
        total=subtotal - discount,
    )


def promotions_for(
    cart: Cart, items: Iterable[CartItem], *, user: Customer = None, email: str = ""
) -> dict[Any, AppliedPromotion]:
    """Promocje pozycji koszyka, z uwzględnieniem kodu aktywowanego w koszyku."""
    return best_promotions(items, user=user, email=email, code_promotion=cart.promotion)


@transaction.atomic
def apply_promotion_code(cart: Cart, code: str) -> Cart:
    """Aktywuje w koszyku promocję kodową; nowy kod zastępuje poprzedni.

    Kod musi należeć do promocji w okresie obowiązywania. Czy promocja
    obejmie którąś pozycję — zakres, limity, próg koszyka — rozstrzyga wycena,
    bo zawartość koszyka jeszcze się zmieni.
    """
    normalised = normalise_code(code)
    promotion = (
        Promotion.objects.active().filter(code=normalised).first()
        if normalised
        else None
    )
    if promotion is None:
        raise CartError({"code": "Nie ma aktywnej promocji o tym kodzie."})
    cart.promotion = promotion
    cart.last_activity_at = timezone.now()
    cart.save(update_fields=["promotion", "last_activity_at", "updated_at"])
    return cart


def get_cart(*, user: Customer = None, token: str | None = None) -> Cart | None:
    """Koszyk konta albo gościa; `None`, gdy żadnego jeszcze nie ma."""
    if user is not None:
        return Cart.objects.filter(user=user).first()
    if token:
        return Cart.objects.guest().filter(session_key=token).first()
    return None


def get_or_create_cart(*, user: Customer = None, token: str | None = None) -> Cart:
    """Koszyk do zapisu — zakładany przy pierwszym dodaniu pozycji (ADR 0030).

    Gość dostaje tu swój token. Token nieznany backendowi nie jest błędem:
    koszyk mógł już wygasnąć albo zostać scalony z kontem, a klient ma wtedy
    zacząć od nowa, a nie zobaczyć 404 przy dodawaniu do koszyka.
    """
    existing = get_cart(user=user, token=token)
    if existing is not None:
        return existing
    if user is not None:
        # `get_or_create`, bo koszyk konta jest relacją jeden-do-jednego:
        # dwa żądania świeżo zalogowanego klienta, które trafią tu naraz,
        # inaczej rozbiłyby się o unikalność zamiast dostać ten sam koszyk.
        cart, _ = Cart.objects.get_or_create(user=user)
        return cart
    return Cart.objects.create(session_key=new_guest_token())


def find_item(
    cart: Cart, variant: ProductVariant, personalisation: Personalisation
) -> CartItem | None:
    """Pozycja o dokładnie tej personalizacji — jedyna, z którą wolno scalać."""
    return CartItem.objects.filter(
        cart=cart, variant=variant, **personalisation.as_fields()
    ).first()


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

    Blokowany jest wiersz koszyka, a nie wiersz pozycji: pozycji może jeszcze
    nie być, a blokada na nieistniejącym wierszu nie blokuje niczego, więc
    dwa równoległe dodania tego samego wyrobu rozbiłyby się o unikalność
    zamiast dołożyć sztukę.
    """
    locked = Cart.objects.select_for_update().get(pk=cart.pk)
    personalisation = Personalisation(
        engraving_text=engraving_text,
        second_size=second_size,
        second_engraving_text=second_engraving_text,
    )

    item = find_item(locked, variant, personalisation)
    wanted = quantity + (item.quantity if item is not None else 0)

    _reject_quantity_above_limit(wanted)
    _reject_quantity_above_stock(variant, wanted)

    if item is None:
        item = CartItem(
            cart=locked,
            variant=variant,
            quantity=wanted,
            **personalisation.as_fields(),
        )
    else:
        item.quantity = wanted
    item.full_clean(exclude=["cart"])
    item.save()
    locked.touch()
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
    o tej samej personalizacji sumują ilości, pozostałe trafiają obok. Token
    gościa przestaje działać razem z jego koszykiem.

    Ilość po scaleniu jest przycinana do limitu sztuk **i** do stanu
    magazynowego, zamiast odrzucać całe scalenie: klient właśnie się
    zalogował i ma zobaczyć swoje rzeczy, a nie błąd. Koszyk gościa mógł
    zresztą leżeć tygodniami, więc jego ilości i tak wymagają sprawdzenia
    na nowo.
    """
    if guest.pk == target.pk:
        return target

    for item in cart_items(guest):
        existing = find_item(target, item.variant, Personalisation.of(item))
        if existing is None:
            item.quantity = _allowed_quantity(item.variant, item.quantity)
            item.cart = target
            item.save(update_fields=["cart", "quantity", "updated_at"])
            continue
        existing.quantity = _allowed_quantity(
            item.variant, existing.quantity + item.quantity
        )
        existing.save(update_fields=["quantity", "updated_at"])
        item.delete()

    # Kod wpisany jako gość nie przepada przy logowaniu, ale nie nadpisuje
    # kodu, który konto już miało.
    if target.promotion_id is None and guest.promotion_id is not None:  # type: ignore[missing-attribute]
        target.promotion_id = guest.promotion_id  # type: ignore[missing-attribute]
        target.save(update_fields=["promotion", "updated_at"])
    guest.delete()
    target.touch()
    return target


def _allowed_quantity(variant: ProductVariant, wanted: int) -> int:
    """Ile sztuk wolno zostawić: nie ponad limit i nie ponad stan.

    Przy stanie zerowym zostaje jedna sztuka, a nie zero: pozycja, której nie
    da się kupić, ma być widoczna w koszyku, żeby klient wiedział, co odpadło
    i sam ją usunął. Złożenie zamówienia i tak jej nie przepuści.
    """
    allowed = min(wanted, MAX_ITEM_QUANTITY)
    available = variant.available
    if available is not None:
        allowed = min(allowed, available)
    return max(allowed, 1)


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
