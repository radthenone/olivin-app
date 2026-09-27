from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q

from apps.consents.models import Consent, ConsentDocument, ConsentKind
from apps.inventory.models import ReservationStatus
from apps.inventory.services import (
    ReservationError,
    consume,
    release,
    reserve,
    restock,
)
from apps.orders.models import (
    GUEST_ORDER_LIMIT,
    Cart,
    CartItem,
    Order,
    OrderItem,
    OrderStatus,
)
from apps.orders.services.cart import cart_items, promotions_for, totals
from apps.orders.services.currency import (
    ConvertedLine,
    convert_cart,
    convert_shipping,
)
from apps.products.models import EURO, ExchangeRate, ProductStatus
from apps.promotions.models import (
    Coupon,
    CouponRedemption,
    CouponStatus,
    Promotion,
    PromotionRedemption,
)
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
    rate = _exchange_rate_for(zone)
    _lock_limited_promotions()
    coupon = _lock_coupon(cart)
    discounts = promotions_for(cart, items, user=user, email=subject_email)
    summary = totals(items, discounts, coupon)
    if rate is not None and summary.coupon_amount:
        # Kupon ma nominał w złotych (ADR 0011) — nie płaci za zamówienie w euro.
        raise OrderError(
            {"coupon": "Kupon w złotych nie opłaci zamówienia w euro — usuń go."}
        )

    _reject_unavailable_items(items)
    _reject_without_terms_consent(user=user, email=subject_email)
    _reject_unavailable_method(shipping_method, order_value=summary.subtotal, zone=zone)

    shipping_cost = cost_for(shipping_method, summary.subtotal)
    # Limit liczony od kwoty do zapłaty, a nie od samego towaru: próg z
    # `.ai/project.md` dotyczy tego, ile gość zostawia w sklepie.
    _reject_guest_above_limit(user=user, total=summary.total + shipping_cost)

    discount = summary.discount_amount
    lines: dict[Any, ConvertedLine] = {}
    if rate is not None:
        # Warunki (limit gościa, próg darmowej dostawy, dostępność metody)
        # liczone w złotych; zamówienie zapisane w euro tą samą funkcją,
        # którą liczy podgląd kasy.
        lines, converted = convert_cart(items, discounts, rate)
        discount = converted.discount_amount
        shipping_cost = convert_shipping(shipping_cost, rate)

    order = _build_order(
        address=address,
        shipping_method=shipping_method,
        shipping_cost=shipping_cost,
        user=user,
        email=subject_email,
        invoice_requested=invoice_requested,
        discount=discount,
        coupon=summary.coupon_amount,
        rate=rate,
    )
    _snapshot_items(order, items, discounts, lines)
    _record_redemptions(order, discounts)
    _redeem_coupon(order, coupon, summary.coupon_amount)
    _reserve_items(order, items)
    if order.total.amount == 0:
        # Nic do zapłaty (kupon + darmowa dostawa): `paid` bez operatora.
        consume_stock(order)
        mark_paid(order)

    cart.items.all().delete()  # type: ignore[missing-attribute]
    # Kod i kupon zostały wykorzystane — następny koszyk zaczyna bez nich.
    cart.promotion = None
    cart.coupon = None
    cart.save(update_fields=["promotion", "coupon", "updated_at"])
    cart.touch()
    return order


@transaction.atomic
def cancel_order(order: Order) -> Order:
    """Anuluje zamówienie i zwalnia rezerwacje.

    `pending` — od razu. `paid` bez żadnej płatności (pokryte w całości
    kuponem) — też od razu: towar wraca na stan, kupon do użycia. Opłacone
    pieniędzmi pociąga zwrot u operatora —
    `apps.payments.services.request_cancellation`.

    Zamówienie wymiany za zwrot (#198) jest zawsze `paid` i zawsze 0 zł, więc
    bez tej odmowy trafiłoby na tę samą ścieżkę co zwykłe zamówienie pokryte
    kuponem: towar wróciłby na stan, a pozycja zwrotu, która je wywołała,
    zostałaby rozliczona jak udana wymiana — klient bez towaru i bez zwrotu
    pieniędzy. Cofnięcie takiego zamówienia idzie przez sklep, nie przez
    samoobsługę klienta.
    """
    if hasattr(order, "return_exchange_item"):
        raise OrderError(
            {
                "status": (
                    "Zamówienie wymiany za zwrot nie podlega samodzielnemu "
                    "anulowaniu — skontaktuj się ze sklepem."
                )
            }
        )
    if is_covered_by_coupon(order):
        _cancel_paid_without_payment(order)
        return order
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


def _lock_coupon(cart: Cart) -> Coupon | None:
    """Kupon koszyka zablokowany do końca transakcji — jednorazowość.

    Dwa koszyki z tym samym kodem składane naraz: drugie zamówienie czeka
    na pierwsze i widzi kupon już wykorzystany. Wtedy odmowa, a nie cicha
    zmiana kwoty — klient widział w koszyku sumę po kuponie.
    """
    if cart.coupon_id is None:  # type: ignore[missing-attribute]
        return None
    coupon = Coupon.objects.select_for_update().filter(pk=cart.coupon_id).first()  # type: ignore[missing-attribute]
    if coupon is None or not coupon.is_usable():
        raise OrderError(
            {
                "coupon": (
                    "Kupon został już wykorzystany albo wygasł — usuń go "
                    "z koszyka i złóż zamówienie ponownie."
                )
            }
        )
    return coupon


def _redeem_coupon(order: Order, coupon: Coupon | None, amount: Money) -> None:
    """Zapisuje użycie kuponu; nadwyżka nominału przepada razem z kuponem."""
    if coupon is None or amount.amount <= 0:
        return
    CouponRedemption.objects.create(coupon=coupon, order=order, amount=amount.amount)
    coupon.status = CouponStatus.REDEEMED
    coupon.save(update_fields=["status", "updated_at"])


def _close_unpaid(order: Order) -> None:
    """Zamyka nieopłacone zamówienie: rezerwacje wracają, status `cancelled`.

    Kupon wraca do użycia — klient nic nie kupił. Wiersz użycia zostaje
    jako ślad (ADR 0014); termin ważności się nie przesuwa.
    """
    release_reservations(order)
    _return_coupon(order)
    order.transition_to(OrderStatus.CANCELLED)


def _cancel_paid_without_payment(order: Order) -> None:
    """Zamówienie pokryte kuponem: towar wraca na stan, kupon do użycia."""
    for reservation in order.reservations.filter(  # type: ignore[missing-attribute]
        status=ReservationStatus.CONSUMED
    ):
        restock(reservation, note=f"Anulowanie zamówienia {order.number}")
    _return_coupon(order)
    order.transition_to(OrderStatus.CANCELLED)


def _return_coupon(order: Order) -> None:
    """Kupon wraca do użycia; wiersz użycia zostaje jako ślad (ADR 0014)."""
    Coupon.objects.filter(
        redemptions__order=order, status=CouponStatus.REDEEMED
    ).update(status=CouponStatus.ISSUED)


def is_covered_by_coupon(order: Order) -> bool:
    """Opłacone bez pieniędzy — kupon pokrył towar, dostawa darmowa.

    Po kwocie, nie po braku płatności: nie ma tu czego zwracać u operatora,
    a zamówienie opłacone pieniędzmi zawsze ma kwotę większą od zera.
    """
    return order.status == OrderStatus.PAID and order.total.amount == 0


def mark_paid(order: Order) -> None:
    """Zamówienie `paid` i dokumenty sprzedaży po commicie (ADR 0026).

    Po commicie: zadanie uruchomione wcześniej mogłoby nie zobaczyć
    zamówienia opłaconego albo wystawić dokument za cofniętą zapłatę.
    """
    # Import w funkcji: `apps.orders.tasks` importuje ten moduł.
    from apps.orders.tasks import issue_sales_documents

    order.transition_to(OrderStatus.PAID)
    transaction.on_commit(
        lambda: issue_sales_documents.delay(str(order.pk))  # type: ignore[missing-attribute]
    )


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
    coupon: Money,
    rate: ExchangeRate | None,
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
        # Kopia kursu: późniejsza zmiana kursu nie rusza zamówienia (ADR 0019).
        exchange_rate=rate.rate if rate is not None else 1,
        exchange_rate_on=rate.effective_on if rate is not None else None,
        exchange_rate_source=rate.source if rate is not None else "",
        terms_document=terms,
        invoice_requested=invoice_requested,
        discount_amount=discount.amount,
        coupon_amount=coupon.amount,
    )


def _exchange_rate_for(zone: ShippingZone) -> ExchangeRate | None:
    """Kurs euro dla strefy EU (ADR 0019); `None` dla sprzedaży w złotych."""
    if zone != ShippingZone.EU:
        return None
    rate = ExchangeRate.objects.current(EURO)
    if rate is None:
        raise OrderError({"currency": "Kurs euro nie jest dostępny — spróbuj później."})
    return rate


def _snapshot_items(
    order: Order,
    items: list[CartItem],
    discounts: Mapping[Any, AppliedPromotion],
    lines: Mapping[Any, ConvertedLine],
) -> None:
    """Przepisuje pozycje koszyka na pozycje zamówienia (ADR 0010).

    `lines` niesie pozycje przeliczone na euro (`convert_cart`); pusty
    słownik oznacza sprzedaż w złotych.
    """
    snapshots = []
    for item in items:
        applied = discounts.get(item.pk)
        variant = item.variant
        product = variant.product
        engraving = product.engraving_price or 0
        unit_price = variant.effective_price.amount
        discount = applied.amount.amount if applied else 0
        line = lines.get(item.pk)
        if line is not None:
            unit_price = line.unit_price.amount
            engraving = line.engraving_unit_price.amount
            discount = line.discount.amount
        snapshots.append(
            OrderItem(
                order=order,
                variant=variant,
                product_name=product.name,
                sku=variant.sku,
                is_made_to_order=product.is_made_to_order,
                quantity=item.quantity,
                unit_price=unit_price,
                vat_rate=variant.vat_rate,
                is_vat_exempt=variant.is_vat_exempt,
                vat_exemption_basis=variant.vat_exemption_basis,
                engraving_text=item.engraving_text,
                engraving_price=engraving if item.engraving_text else 0,
                size=variant.size,
                second_size=item.second_size,
                second_engraving_text=item.second_engraving_text,
                discount_amount=discount,
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


def _needed_stock(order: Order) -> Counter[int]:
    """Ilości do zdjęcia ze stanu według wariantu; wyrób na zamówienie pomija."""
    needed: Counter[int] = Counter()
    for item in order.items.all():  # type: ignore[missing-attribute]
        if not item.is_made_to_order:
            needed[item.variant_id] += item.quantity * item.specimen_count  # type: ignore[missing-attribute]
    return needed


def consume_stock(order: Order) -> None:
    """Rozlicza rezerwacje ruchem sprzedaży.

    Rezerwacja wygasła, zanim zdarzenie doszło (np. długie uwierzytelnienie
    u banku) — próbujemy wziąć towar od nowa. Jeśli już go nie ma,
    `ReservationError` wychodzi na zewnątrz i pieniądze wracają.
    Wspólne dla zapłaty u operatora i zamówienia pokrytego kuponem.
    """
    needed = _needed_stock(order)
    for reservation in order.reservations.filter(  # type: ignore[missing-attribute]
        status=ReservationStatus.ACTIVE
    ).select_related("variant__product"):
        if reservation.is_active:
            consume(reservation)
            needed[reservation.variant_id] -= reservation.quantity
        else:
            release(reservation)

    variants = {
        item.variant_id: item.variant  # type: ignore[missing-attribute]
        for item in order.items.select_related("variant__product")  # type: ignore[missing-attribute]
    }
    for variant_id, quantity in needed.items():
        if quantity > 0:
            reservation = reserve(variants[variant_id], quantity, order=order)
            if reservation is not None:
                consume(reservation)
