from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q

from apps.consents.models import Consent, ConsentDocument, ConsentKind
from apps.inventory.models import ReservationStatus
from apps.inventory.services import ReservationError, release, reserve
from apps.orders.models import (
    GUEST_ORDER_LIMIT,
    Cart,
    CartItem,
    Order,
    OrderItem,
    OrderStatus,
)
from apps.orders.services.cart import cart_items, promotions_for, totals
from apps.products.models import ProductStatus
from apps.promotions.models import Promotion, PromotionRedemption
from apps.promotions.services import AppliedPromotion
from apps.shipping.models import ShippingMethod, ShippingZone
from apps.shipping.services import cost_for, zone_for_country
from common.money import DEFAULT_CURRENCY, Money

if TYPE_CHECKING:
    from apps.accounts.models import Customer, CustomUser


class OrderError(ValidationError):
    """Odmowa złożenia albo zmiany zamówienia, którą klient widzi jako 400."""


@dataclass(frozen=True, slots=True)
class ShippingAddress:
    """Adres dostawy przepisywany do zamówienia (ADR 0010).

    Osobny typ, nie słownik: te pola chodzą razem przez serializer, walidację
    strefy i snapshot, a słownik gubiłby literówkę w nazwie klucza dopiero
    przy zapisie.
    """

    recipient_name: str
    street: str
    city: str
    postal_code: str
    country: str
    street2: str = ""


@transaction.atomic
def create_order(
    *,
    cart: Cart,
    address: ShippingAddress,
    shipping_method: ShippingMethod,
    user: Customer = None,
    email: str = "",
    invoice_requested: bool = False,
) -> Order:
    """Składa zamówienie z koszyka w jednej transakcji (ADR 0030).

    Kolejność ma znaczenie: najpierw sprawdzenia, które mogą odmówić, potem
    snapshot, rezerwacje i dopiero na końcu czyszczenie koszyka. Gdyby
    cokolwiek padło po drodze, transakcja cofa całość — klient nie zostaje
    ani z pustym koszykiem bez zamówienia, ani z zamówieniem bez rezerwacji.
    """
    items = list(cart_items(cart))
    if not items:
        raise OrderError({"cart": "Nie da się złożyć zamówienia z pustego koszyka."})

    subject_email = _resolve_email(user=user, email=email)
    zone = zone_for_country(address.country)
    if zone is None:
        raise OrderError(
            {"country": "Sklep wysyła wyłącznie do Polski i pozostałych krajów Unii."}
        )
    _lock_limited_promotions()
    discounts = promotions_for(cart, items, user=user, email=subject_email)
    summary = totals(items, discounts)

    _reject_unavailable_items(items)
    _reject_without_terms_consent(user=user, email=subject_email)
    _reject_unavailable_method(shipping_method, order_value=summary.subtotal, zone=zone)

    shipping_cost = cost_for(shipping_method, summary.subtotal)
    # Limit liczony od kwoty do zapłaty, a nie od samego towaru: próg z
    # `.ai/project.md` dotyczy tego, ile gość zostawia w sklepie.
    _reject_guest_above_limit(user=user, total=summary.total + shipping_cost)

    order = _build_order(
        address=address,
        shipping_method=shipping_method,
        shipping_cost=shipping_cost,
        user=user,
        email=subject_email,
        invoice_requested=invoice_requested,
        discount=summary.discount_amount,
    )
    _snapshot_items(order, items, discounts)
    _record_redemptions(order, discounts)
    _reserve_items(order, items)

    cart.items.all().delete()  # type: ignore[missing-attribute]
    # Kod został wykorzystany — następny koszyk zaczyna bez niego.
    cart.promotion = None
    cart.save(update_fields=["promotion", "updated_at"])
    cart.touch()
    return order


@transaction.atomic
def cancel_order(order: Order) -> Order:
    """Anuluje zamówienie i zwalnia rezerwacje.

    Tylko `pending`: anulowanie zamówienia opłaconego pociąga zwrot pieniędzy
    u operatora — `apps.payments.services.request_cancellation`.
    """
    if order.status != OrderStatus.PENDING:
        raise OrderError(
            {
                "status": (
                    f"Anulować można wyłącznie zamówienie oczekujące na zapłatę; "
                    f"to jest „{order.get_status_display()}”."  # type: ignore[missing-attribute]
                )
            }
        )

    _close_unpaid(order)
    return order


def release_reservations(order: Order) -> int:
    """Zwalnia wszystkie rezerwacje zamówienia; zwraca liczbę zwolnionych.

    Rezerwacja już zwolniona albo przeterminowana nie jest tu błędem —
    zamówienie anulowane po upływie pół godziny to normalny przypadek, nie
    wyjątkowy.
    """
    released = 0
    active = order.reservations.filter(  # type: ignore[missing-attribute]
        status=ReservationStatus.ACTIVE
    )
    for reservation in active:
        release(reservation)
        released += 1
    return released


def attach_guest_orders(user: CustomUser, email: str | None = None) -> int:
    """Podpina zamówienia gościa do konta na ten sam, **potwierdzony** adres.

    Adres jest jedynym łącznikiem, jaki mamy — gość nie ma konta, a token
    koszyka znika razem z koszykiem. Zgoda gościa **nie** przechodzi na konto
    (`CONTEXT.md`, Consent), ale zamówienie owszem: to jego zakup, nie jego
    oświadczenie woli.

    Adres podaje się osobno, bo konto może mieć ich kilka i podpinać wolno
    tylko ten, który klient właśnie potwierdził.
    """
    address = email or user.email
    return Order.objects.filter(user__isnull=True, email__iexact=address).update(
        user=user
    )


def _lock_limited_promotions() -> None:
    """Blokuje promocje z limitem do końca transakcji składania zamówienia.

    Bez tego dwa równoległe zamówienia policzyłyby te same wolne użycia
    i oba dostałyby rabat ponad limit.
    """
    # ponytail: blokada na wszystkie aktywne promocje z limitem szereguje
    # zamówienia korzystające z nich; przy dużym ruchu blokować tylko wybrane.
    list(
        Promotion.objects.active()
        .filter(Q(global_limit__isnull=False) | Q(per_customer_limit__isnull=False))
        .select_for_update()
        .values_list("pk", flat=True)
    )


def _record_redemptions(
    order: Order, discounts: Mapping[Any, AppliedPromotion]
) -> None:
    """Jedno zastosowanie na promocję — z sumą jej rabatu na wszystkich pozycjach."""
    amounts: dict[Promotion, int] = defaultdict(int)
    for applied in discounts.values():
        amounts[applied.promotion] += applied.amount.amount
    PromotionRedemption.objects.bulk_create(
        PromotionRedemption(promotion=promotion, order=order, amount=amount)
        for promotion, amount in amounts.items()
    )


def _close_unpaid(order: Order) -> None:
    """Zamyka nieopłacone zamówienie: rezerwacje wracają, status `cancelled`."""
    release_reservations(order)
    order.transition_to(OrderStatus.CANCELLED)


def _resolve_email(*, user: Customer, email: str) -> str:
    """E-mail zamówienia: z konta albo podany przez gościa.

    Zawsze wypełniony, także dla zalogowanego — zamówienie ma zostać czytelne
    po anonimizacji konta (`CONTEXT.md`, Account anonymisation).
    """
    if user is not None:
        return user.email
    if not email:
        raise OrderError({"email": "Gość podaje adres, pod który idzie potwierdzenie."})
    return email


def _reject_unavailable_items(items: list[CartItem]) -> None:
    """Pozycja bez stanu zatrzymuje całe zamówienie, a nie znika po cichu.

    Koszyk mógł leżeć tygodniami, a stan w międzyczasie zejść. Klient ma
    zobaczyć, czego zabrakło, zanim zapłaci — nie po fakcie.
    """
    for item in items:
        product = item.variant.product
        if product.status != ProductStatus.PUBLISHED:
            raise OrderError(
                {
                    "items": (
                        f"{item.variant.sku} nie jest już w sprzedaży — usuń "
                        "pozycję z koszyka."
                    )
                }
            )
        available = item.variant.available
        if available is None:
            continue
        if item.quantity * item.specimen_count > available:
            raise OrderError(
                {
                    "items": (
                        f"{item.variant.sku}: na stanie jest {available} szt., "
                        f"a w koszyku {item.quantity}."
                    )
                }
            )


def _reject_without_terms_consent(*, user: Customer, email: str) -> None:
    """Bez akceptacji bieżącej wersji regulaminu nie ma zamówienia."""
    # Konto ma pierwszeństwo przed adresem (`for_subject`): zgoda gościa nie
    # przechodzi na konto założone później na ten sam e-mail.
    if not Consent.objects.has_current_consent(
        ConsentKind.TERMS, user=user, email=email
    ):
        raise OrderError(
            {
                "terms": (
                    "Złożenie zamówienia wymaga akceptacji bieżącej wersji regulaminu."
                )
            }
        )


def _reject_guest_above_limit(*, user: Customer, total: Money) -> None:
    if user is not None:
        return
    if total.amount > GUEST_ORDER_LIMIT:
        limit = Money(GUEST_ORDER_LIMIT, total.currency)
        raise OrderError(
            {
                "email": (
                    f"Zamówienie powyżej {limit} wymaga konta — załóż je i złóż "
                    "zamówienie ponownie."
                )
            }
        )


def _reject_unavailable_method(
    method: ShippingMethod, *, order_value: Money, zone: ShippingZone
) -> None:
    """Metoda musi być tą samą, którą klient zobaczył w kroku dostawy.

    Sprawdzane po raz drugi, choć krok trzeci kasy pokazał już listę: między
    wyborem a zapłatą klient mógł zmienić adres albo zawartość koszyka,
    a metoda wygaszona w panelu znika z oferty od razu (ADR 0028).
    """
    if not method.is_active:
        raise OrderError(
            {"shipping_method": "Ta metoda dostawy nie jest już dostępna."}
        )
    if method.zone != zone:
        raise OrderError(
            {"shipping_method": "Ta metoda dostawy nie obsługuje kraju odbiorcy."}
        )
    if method.currency != order_value.currency:
        raise OrderError(
            {"shipping_method": "Metoda dostawy jest wyceniona w innej walucie."}
        )
    limit = method.max_order_value_money
    if limit is not None and order_value > limit:
        raise OrderError(
            {
                "shipping_method": (
                    f"Ta metoda obsługuje zamówienia do {limit}; wybierz inną."
                )
            }
        )


def _build_order(
    *,
    address: ShippingAddress,
    shipping_method: ShippingMethod,
    shipping_cost: Money,
    user: Customer,
    email: str,
    invoice_requested: bool,
    discount: Money,
) -> Order:
    terms = ConsentDocument.objects.current(ConsentKind.TERMS)
    if terms is None:
        raise OrderError({"terms": "Sklep nie ma obowiązującej wersji regulaminu."})

    return Order.objects.create(
        user=user,
        email=email,
        recipient_name=address.recipient_name,
        street=address.street,
        street2=address.street2,
        city=address.city,
        postal_code=address.postal_code,
        country=address.country,
        shipping_method=shipping_method,
        shipping_method_name=shipping_method.name,
        shipping_cost=shipping_cost.amount,
        currency=shipping_cost.currency or DEFAULT_CURRENCY,
        terms_document=terms,
        invoice_requested=invoice_requested,
        discount_amount=discount.amount,
    )


def _snapshot_items(
    order: Order, items: list[CartItem], discounts: Mapping[Any, AppliedPromotion]
) -> None:
    """Przepisuje pozycje koszyka na pozycje zamówienia (ADR 0010)."""
    snapshots = []
    for item in items:
        applied = discounts.get(item.pk)
        variant = item.variant
        product = variant.product
        engraving = product.engraving_price or 0
        snapshots.append(
            OrderItem(
                order=order,
                variant=variant,
                product_name=product.name,
                sku=variant.sku,
                is_made_to_order=product.is_made_to_order,
                quantity=item.quantity,
                unit_price=variant.effective_price.amount,
                vat_rate=variant.vat_rate,
                is_vat_exempt=variant.is_vat_exempt,
                vat_exemption_basis=variant.vat_exemption_basis,
                engraving_text=item.engraving_text,
                engraving_price=engraving if item.engraving_text else 0,
                size=variant.size,
                second_size=item.second_size,
                second_engraving_text=item.second_engraving_text,
                discount_amount=applied.amount.amount if applied else 0,
            )
        )
    OrderItem.objects.bulk_create(snapshots)


def _reserve_items(order: Order, items: list[CartItem]) -> None:
    """Zakłada rezerwacje na czas płatności (`CONTEXT.md`, Reservation).

    Wyrób na zamówienie rezerwacji nie dostaje — `reserve()` zwraca wtedy
    `None` i to jest poprawny wynik, nie odmowa (ADR 0024).
    """
    for item in items:
        try:
            reserve(
                item.variant,
                item.quantity * item.specimen_count,
                order=order,
            )
        except ReservationError as error:
            raise OrderError({"items": str(error)}) from error


def expire_unpaid_orders(*, older_than: datetime) -> int:
    """Anuluje zamówienia `pending` starsze niż podana chwila; zwraca ich liczbę."""
    stale = Order.objects.unpaid_since(older_than)
    cancelled = 0
    for order in stale:
        _close_unpaid(order)
        cancelled += 1
    return cancelled
