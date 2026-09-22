from __future__ import annotations

from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction

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
from apps.orders.services.cart import cart_items, totals
from apps.products.models import ProductStatus
from apps.shipping.models import ShippingMethod, ShippingZone
from apps.shipping.services import cost_for
from common.money import DEFAULT_CURRENCY, Money

# Kraje Unii poza Polską. Lista jest tu, a nie w bazie, bo zmienia się raz na
# dekadę i jest faktem prawnym, a nie danymi sklepu (ADR 0019).
EU_COUNTRIES = frozenset(
    {
        "AT",
        "BE",
        "BG",
        "CY",
        "CZ",
        "DE",
        "DK",
        "EE",
        "ES",
        "FI",
        "FR",
        "GR",
        "HR",
        "HU",
        "IE",
        "IT",
        "LT",
        "LU",
        "LV",
        "MT",
        "NL",
        "PT",
        "RO",
        "SE",
        "SI",
        "SK",
    }
)


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


def resolve_zone(country: str) -> str:
    """Strefa dla kraju; kraj spoza Unii nie jest obsługiwany (ADR 0019)."""
    if country == "PL":
        return ShippingZone.PL
    if country in EU_COUNTRIES:
        return ShippingZone.EU
    raise OrderError(
        {"country": "Sklep wysyła wyłącznie do Polski i pozostałych krajów Unii."}
    )


@transaction.atomic
def create_order(
    *,
    cart: Cart,
    address: ShippingAddress,
    shipping_method: ShippingMethod,
    user=None,
    email: str = "",
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
    zone = resolve_zone(address.country)
    summary = totals(items)

    _reject_unavailable_items(items)
    _reject_without_terms_consent(user=user, email=subject_email)
    _reject_unavailable_method(shipping_method, order_value=summary.subtotal, zone=zone)

    shipping_cost = cost_for(shipping_method, summary.subtotal)
    # Limit liczony od kwoty do zapłaty, a nie od samego towaru: próg z
    # `.ai/project.md` dotyczy tego, ile gość zostawia w sklepie.
    _reject_guest_above_limit(user=user, total=summary.subtotal + shipping_cost)

    order = _build_order(
        address=address,
        shipping_method=shipping_method,
        shipping_cost=shipping_cost,
        user=user,
        email=subject_email,
    )
    _snapshot_items(order, items)
    _reserve_items(order, items)

    cart.items.all().delete()  # type: ignore[missing-attribute]
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

    release_reservations(order)
    order.transition_to(OrderStatus.CANCELLED)
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


def attach_guest_orders(user, email: str | None = None) -> int:
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


def _resolve_email(*, user, email: str) -> str:
    """E-mail zamówienia: z konta albo podany przez gościa.

    Zawsze wypełniony, także dla zalogowanego — zamówienie ma zostać czytelne
    po anonimizacji konta (`CONTEXT.md`, Account anonymisation).
    """
    if user is not None and user.is_authenticated:
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


def _reject_without_terms_consent(*, user, email: str) -> None:
    """Bez akceptacji bieżącej wersji regulaminu nie ma zamówienia."""
    subject = {"user": user} if user is not None and user.is_authenticated else {}
    if not subject:
        subject = {"email": email}
    if not Consent.objects.has_current_consent(ConsentKind.TERMS, **subject):
        raise OrderError(
            {
                "terms": (
                    "Złożenie zamówienia wymaga akceptacji bieżącej wersji regulaminu."
                )
            }
        )


def _reject_guest_above_limit(*, user, total: Money) -> None:
    if user is not None and user.is_authenticated:
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
    method: ShippingMethod, *, order_value: Money, zone: str
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
    user,
    email: str,
) -> Order:
    terms = ConsentDocument.objects.current(ConsentKind.TERMS)
    if terms is None:
        raise OrderError({"terms": "Sklep nie ma obowiązującej wersji regulaminu."})

    return Order.objects.create(
        user=user if user is not None and user.is_authenticated else None,
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
    )


def _snapshot_items(order: Order, items: list[CartItem]) -> None:
    """Przepisuje pozycje koszyka na pozycje zamówienia (ADR 0010)."""
    snapshots = []
    for item in items:
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


def expire_unpaid_orders(*, older_than) -> int:
    """Anuluje zamówienia `pending` starsze niż podana chwila; zwraca ich liczbę."""
    stale = Order.objects.unpaid_since(older_than)
    cancelled = 0
    for order in stale:
        release_reservations(order)
        order.transition_to(OrderStatus.CANCELLED)
        cancelled += 1
    return cancelled
