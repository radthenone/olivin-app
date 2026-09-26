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
    ReturnRefundStatus,
    ReturnRequest,
    ReturnRequestItem,
)
from apps.promotions.models import COUPON_NOMINAL_STEP, Coupon, CouponSource

# Uwzględniona naprawa oddaje towar, nie pieniądze — zawsze. Wymiana też,
# ale tylko gdy faktycznie doszła do skutku (jest zamówienie wymiany,
# `services.exchange`, #198) — bez stanu magazynowego pozycja rozlicza się
# jak zwykły zwrot pieniędzy.


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
    razu; zwrot pieniędzy (`refund_return_request`), korekta i powiadomienie
    idą po zatwierdzeniu zapisu.
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
    # Kupon zaokrąglony w górę oddał więcej, niż był wart zwrot — nadwyżkę
    # potrąca się z pieniędzy przy kolejnym zwrocie. Pieniędzy nigdy nie
    # oddaje się więcej, niż klient faktycznie zapłacił.
    before = (
        ReturnRequest.objects.filter(order=order, settled_at__isnull=False)
        .exclude(pk=request.pk)
        .aggregate(value=Sum("compensation_amount"), refunded=Sum("refund_amount"))
    )
    refunded_before = before["refunded"] or 0
    overpaid = max(issued + refunded_before - (before["value"] or 0), 0)
    paid_left = max(order.total.amount - refunded_before, 0)
    money = max(min(money - overpaid, paid_left), 0)
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
    if money:
        request.refund_status = ReturnRefundStatus.PENDING
    request.save(
        update_fields=[
            "coupon",
            "compensation_amount",
            "refund_amount",
            "refund_status",
            "settled_at",
            "updated_at",
        ]
    )
    # Import w funkcji: `apps.payments` i `apps.orders.tasks` importują serwisy
    # zamówień. Zwrot u operatora dopiero po zatwierdzeniu — cofnięta
    # transakcja nie może zostawić pieniędzy wypłaconych bez śladu w bazie.
    from apps.orders.tasks import issue_return_correction
    from apps.payments.tasks import refund_return_request

    if money:
        transaction.on_commit(
            lambda: refund_return_request.delay(str(request.pk))  # type: ignore[missing-attribute]
        )

    transaction.on_commit(
        lambda: issue_return_correction.delay(str(request.pk))  # type: ignore[missing-attribute]
    )
    _notify_settled(request)


def exclude_not_refunded(
    items: QuerySet[ReturnRequestItem],
) -> QuerySet[ReturnRequestItem]:
    """Odsiewa naprawę i udaną wymianę — reszta liczy się jak zwrot pieniędzy.

    Publiczne, bo tej samej reguły używa `services.returns` przy sprawdzaniu,
    czy zamówienie ma przejść w `returned` (#198) — dwie kopie tej samej
    definicji rozjechałyby się przy kolejnej zmianie.
    """
    return items.exclude(claim_request=ClaimRequest.REPAIR).exclude(
        claim_request=ClaimRequest.REPLACEMENT, exchange_order__isnull=False
    )


def refunded_items(request: ReturnRequest) -> QuerySet[ReturnRequestItem]:
    """Przyjęte pozycje, za które oddaje się wartość — bez naprawy i udanej wymiany."""
    return exclude_not_refunded(
        request.items.filter(status=ReturnItemStatus.ACCEPTED)  # type: ignore[missing-attribute]
    ).select_related("order_item__order")


def item_value(item: ReturnRequestItem) -> int:
    """Wartość pozycji po promocjach; przy uzgodnieniu — uzgodniona kwota.

    Część ilości liczy się narastająco: udział wszystkiego, co zwrócono do
    tej porcji włącznie, minus udział tego, co przed nią. Zaokrąglenia się
    wtedy znoszą i porcje razem dają dokładnie wartość pozycji.
    """
    if item.agreed_amount is not None:
        return item.agreed_amount
    order_item = item.order_item
    total = order_item.discounted_total

    def share(quantity: int) -> int:
        return total.multiply(Decimal(quantity) / Decimal(order_item.quantity)).amount

    before = _returned_before(item)
    return share(before + item.quantity) - share(before)


def _returned_before(item: ReturnRequestItem) -> int:
    """Ilość pozycji rozliczona we wcześniejszych zgłoszeniach."""
    earlier = ReturnRequestItem.objects.filter(
        order_item=item.order_item,
        status=ReturnItemStatus.ACCEPTED,
        return_request__settled_at__isnull=False,
    ).exclude(return_request=item.return_request_id)  # type: ignore[missing-attribute]
    settled_at = item.return_request.settled_at
    if settled_at is not None:
        earlier = earlier.filter(return_request__settled_at__lt=settled_at)
    return exclude_not_refunded(earlier).aggregate(total=Sum("quantity"))["total"] or 0


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
