"""Rozliczenie przyjętego zwrotu: najpierw kupon, resztę pieniędzmi (ADR 0031)."""

from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import QuerySet, Sum
from django.utils import timezone

from apps.notifications.models import NotificationKind
from apps.notifications.services import notify
from apps.orders.models import (
    ClaimRequest,
    Order,
    ReturnItemStatus,
    ReturnReason,
    ReturnRequest,
    ReturnRequestItem,
)
from apps.promotions.models import COUPON_NOMINAL_STEP, Coupon, CouponSource

# Uwzględniona naprawa albo wymiana oddaje towar, nie pieniądze.
_NOT_REFUNDED_CLAIMS = (ClaimRequest.REPAIR, ClaimRequest.REPLACEMENT)


def split_compensation(amount: int, coupon_left: int) -> tuple[int, int]:
    """Podział kwoty zwrotu (grosze) na nominał kuponu i część pieniężną.

    Kupon bierze najpierw niezwróconą kuponową część zamówienia, zaokrągloną
    w górę do pełnych 10 zł, ale nigdy ponad tę część. Nominał to wielokrotność
    10 zł, więc gdy pozostała część nią nie jest, kupon schodzi do pełnych
    10 zł w dół, a resztę oddają pieniądze — klient nie traci ani grosza.
    """
    step = COUPON_NOMINAL_STEP
    wanted = -(-min(amount, coupon_left) // step) * step
    coupon = min(wanted, coupon_left // step * step)
    return coupon, max(amount - coupon, 0)


def settle_return_request(request: ReturnRequest) -> None:
    """Rozlicza rozpatrzone zgłoszenie; bez kwoty do oddania — nic nie robi.

    Wołane pod blokadą zamówienia (`decide_return_item`), więc kolejne
    zgłoszenie widzi kupony wydane przez wcześniejsze. Kupon powstaje od
    razu; pieniądze zleca `refund_return`, a korekta i powiadomienie idą po
    zatwierdzeniu zapisu.
    """
    if request.settled_at is not None:
        return
    order = request.order
    amount = sum(item_value(item) for item in refunded_items(request))
    if request.reason == ReturnReason.WITHDRAWAL and _withdrawal_covers_order(order):
        amount += order.shipping_cost
    if amount <= 0:
        return

    issued = (
        Coupon.objects.filter(source_order=order, source=CouponSource.RETURN).aggregate(
            total=Sum("nominal")
        )["total"]
        or 0
    )
    coupon_part, money = split_compensation(
        amount, max(order.coupon_amount - issued, 0)
    )
    if coupon_part:
        request.coupon = Coupon.objects.create(
            nominal=coupon_part,
            currency=order.currency,
            source=CouponSource.RETURN,
            source_order=order,
        )
    request.compensation_amount = amount
    request.refund_amount = money
    request.settled_at = timezone.now()
    request.save(
        update_fields=[
            "coupon",
            "compensation_amount",
            "refund_amount",
            "settled_at",
            "updated_at",
        ]
    )
    if money:
        # Import w funkcji: `apps.payments.services` importuje serwisy zamówień.
        from apps.payments.services import refund_return

        refund_return(request)

    from apps.orders.tasks import issue_return_correction

    transaction.on_commit(
        lambda: issue_return_correction.delay(str(request.pk))  # type: ignore[missing-attribute]
    )
    _notify_settled(request)


def refunded_items(request: ReturnRequest) -> QuerySet[ReturnRequestItem]:
    """Przyjęte pozycje, za które oddaje się wartość — bez naprawy i wymiany."""
    return (
        request.items.filter(status=ReturnItemStatus.ACCEPTED)  # type: ignore[missing-attribute]
        .exclude(claim_request__in=_NOT_REFUNDED_CLAIMS)
        .select_related("order_item__order")
    )


def item_value(item: ReturnRequestItem) -> int:
    """Wartość pozycji po promocjach; przy uzgodnieniu — uzgodniona kwota."""
    if item.agreed_amount is not None:
        return item.agreed_amount
    order_item = item.order_item
    if item.quantity == order_item.quantity:
        return order_item.discounted_total.amount
    return order_item.discounted_total.multiply(
        Decimal(item.quantity) / Decimal(order_item.quantity)
    ).amount


def _withdrawal_covers_order(order: Order) -> bool:
    """Czy przyjęte odstąpienia objęły wszystkie pozycje — wtedy wraca dostawa."""
    accepted = dict(
        ReturnRequestItem.objects.filter(
            return_request__order=order,
            return_request__reason=ReturnReason.WITHDRAWAL,
            status=ReturnItemStatus.ACCEPTED,
        )
        .values_list("order_item")
        .annotate(total=Sum("quantity"))
        .order_by()
    )
    return all(
        accepted.get(item.pk, 0) >= item.quantity
        for item in order.items.all()  # type: ignore[missing-attribute]
    )


def compensation_form(request: ReturnRequest) -> str:
    """Forma rekompensaty słowami — do powiadomienia i korekty."""
    parts = []
    if request.coupon is not None:
        parts.append(
            f"kupon {request.coupon.nominal_money} (kod {request.coupon.code})"
        )
    if request.refund_amount:
        parts.append(f"zwrot pieniędzy {request.refund_money}")
    return ", ".join(parts)


def _notify_settled(request: ReturnRequest) -> None:
    """Transakcyjne powiadomienie z kwotą i formą zwrotu, po zatwierdzeniu zapisu."""
    order = request.order
    coupon = request.coupon
    payload = {
        "order_number": order.number,
        "return_request_id": str(request.pk),
        "compensation_amount": str(request.compensation_money),
        "coupon_amount": str(coupon.nominal_money) if coupon else "",
        "coupon_code": coupon.code if coupon else "",
        "refund_amount": str(request.refund_money),
        "refund_status_label": request.get_refund_status_display(),  # type: ignore[missing-attribute]
        "compensation_form": compensation_form(request),
    }
    recipient = order.user if order.user_id is not None else order.email  # type: ignore[missing-attribute]
    transaction.on_commit(
        lambda: notify(
            recipient,  # type: ignore[bad-argument-type]
            NotificationKind.RETURN_SETTLED,
            payload,
            email=order.email,
        ),
        robust=True,
    )
