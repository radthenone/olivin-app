"""Zgłoszenie zwrotu: dopuszczalność, terminy i decyzja per pozycja (#196).

Rozliczenie pieniędzy i kuponów (ADR 0031) oraz wymiana to osobne etapy —
tu powstaje zgłoszenie i decyzja sklepu, nic więcej.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.inventory.models import InventoryItem, StockMovement, StockMovementReason
from apps.notifications.models import NotificationKind
from apps.notifications.services import notify
from apps.orders.models import (
    OPEN_ITEM_STATUSES,
    ClaimRequest,
    Order,
    OrderItem,
    OrderStatus,
    ReturnItemStatus,
    ReturnReason,
    ReturnRequest,
    ReturnRequestItem,
    ReturnRequestStatus,
)
from apps.orders.models.returns import COMPLAINT_YEARS, RETURN_PERIODS


@dataclass(frozen=True)
class ReturnLine:
    """Pozycja zamówienia i ilość, którą klient chce zwrócić."""

    order_item: OrderItem
    quantity: int
    claim_request: str = ""


@dataclass(frozen=True)
class ReturnOption:
    """Co formularz zwrotu może zaproponować dla jednej pozycji."""

    item: OrderItem
    returnable_quantity: int
    deadlines: dict[str, datetime]
    claim_requests: list[str]

    @property
    def deadline_rows(self) -> list[dict[str, object]]:
        """Terminy jako lista par — kształt dla API."""
        return [
            {"reason": reason, "deadline": deadline}
            for reason, deadline in self.deadlines.items()
        ]


def return_deadline(order: Order, reason: str) -> datetime:
    """Koniec terminu danej podstawy, liczony od doręczenia.

    Reklamacja to dwa lata kalendarzowe: doręczenie 29 lutego kończy termin
    28 lutego, a nie przesuwa go o dzień przez rok przestępny.
    """
    delivered_at = order.delivered_at
    assert delivered_at is not None
    if reason != ReturnReason.COMPLAINT:
        return delivered_at + RETURN_PERIODS[reason]
    year = delivered_at.year + COMPLAINT_YEARS
    try:
        return delivered_at.replace(year=year)
    except ValueError:
        return delivered_at.replace(year=year, day=28)


def is_engraved(item: OrderItem) -> bool:
    return bool(item.engraving_text or item.second_engraving_text)


def is_personalised(item: OrderItem) -> bool:
    """Grawer i produkt na zamówienie wyłączają odstąpienie i powrót na stan."""
    return is_engraved(item) or item.is_made_to_order


def claim_requests_for(item: OrderItem) -> list[str]:
    """Żądania reklamacyjne pozycji: zwrot zawsze, reszta według flag produktu."""
    product = item.variant.product
    claims: list[str] = [ClaimRequest.REFUND]
    if product.repair_available:
        claims.append(ClaimRequest.REPAIR)
    if product.replacement_available:
        claims.append(ClaimRequest.REPLACEMENT)
    return claims


def returnable_quantity(item: OrderItem) -> int:
    """Ilość pozycji nieobjęta żadnym nieodrzuconym zgłoszeniem."""
    taken = (
        ReturnRequestItem.objects.filter(order_item=item)
        .exclude(status=ReturnItemStatus.REJECTED)
        .aggregate(total=Sum("quantity"))["total"]
    )
    return item.quantity - (taken or 0)


def return_options(order: Order, *, now: datetime | None = None) -> list[ReturnOption]:
    """Formularz zwrotu: pozycje, otwarte podstawy z terminami i żądania."""
    if order.status != OrderStatus.DELIVERED or order.delivered_at is None:
        return []
    now = now or timezone.now()
    options = []
    for item in order.items.select_related("variant__product"):  # type: ignore[missing-attribute]
        deadlines: dict[str, datetime] = {
            reason: deadline
            for reason in ReturnReason
            if _reason_allowed(item, reason)
            and now <= (deadline := return_deadline(order, reason))
        }
        options.append(
            ReturnOption(
                item=item,
                returnable_quantity=returnable_quantity(item),
                deadlines=deadlines,
                claim_requests=claim_requests_for(item),
            )
        )
    return options


def create_return_request(
    order: Order, *, reason: str, lines: list[ReturnLine]
) -> ReturnRequest:
    """Składa zgłoszenie zwrotu, odrzucając to, czego prawo ani sklep nie dają.

    Zamówienie jest blokowane na czas zapisu: dwa równoległe zgłoszenia tej
    samej pozycji nie mogą razem przekroczyć kupionej ilości.
    """
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order.pk)
        _validate_request(order, reason, lines)
        request = ReturnRequest.objects.create(order=order, reason=reason)
        for line in lines:
            ReturnRequestItem.objects.create(
                return_request=request,
                order_item=line.order_item,
                quantity=line.quantity,
                claim_request=line.claim_request,
                status=(
                    ReturnItemStatus.TO_AGREE
                    if is_engraved(line.order_item) and reason != ReturnReason.COMPLAINT
                    else ReturnItemStatus.PENDING
                ),
            )
        _notify(request)
    return request


def validate_decision(
    item: ReturnRequestItem,
    *,
    status: str,
    restock: bool = False,
    note: str = "",
    agreed_resolution: str = "",
    agreed_amount: int | None = None,
) -> None:
    """Sprawdza decyzję sklepu o pozycji — wspólne dla serwisu i panelu."""
    if not item.is_open:
        raise ValidationError(
            {"status": "Pozycja jest już rozstrzygnięta — decyzji się nie zmienia."}
        )
    if status not in (ReturnItemStatus.ACCEPTED, ReturnItemStatus.REJECTED):
        raise ValidationError(
            {"status": "Decyzja to przyjęcie albo odrzucenie pozycji."}
        )
    if status == ReturnItemStatus.REJECTED and not note.strip():
        raise ValidationError({"decision_note": "Odrzucenie wymaga uzasadnienia."})
    if (
        status == ReturnItemStatus.ACCEPTED
        and item.status == ReturnItemStatus.TO_AGREE
        and (not agreed_resolution.strip() or agreed_amount is None)
    ):
        raise ValidationError(
            {
                "agreed_resolution": (
                    "Pozycja do uzgodnienia wymaga uzgodnionej formy i kwoty."
                )
            }
        )
    if restock and status != ReturnItemStatus.ACCEPTED:
        raise ValidationError(
            {"restocked": "Na stan wraca wyłącznie przyjęta pozycja."}
        )
    if restock and is_personalised(item.order_item):
        raise ValidationError(
            {
                "restocked": (
                    "Wyrób z grawerunkiem ani produkt na zamówienie nie wraca na stan."
                )
            }
        )


def decide_return_item(
    item: ReturnRequestItem,
    *,
    status: str,
    restock: bool = False,
    note: str = "",
    agreed_resolution: str = "",
    agreed_amount: int | None = None,
) -> ReturnRequestItem:
    """Rozstrzyga pozycję zgłoszenia; przyjęta może wrócić na stan.

    Wiersz jest blokowany i sprawdzany ponownie w transakcji — dwie decyzje
    naraz zapisałyby dwa ruchy `return` za ten sam towar.
    """
    with transaction.atomic():
        item = ReturnRequestItem.objects.select_for_update().get(pk=item.pk)
        validate_decision(
            item,
            status=status,
            restock=restock,
            note=note,
            agreed_resolution=agreed_resolution,
            agreed_amount=agreed_amount,
        )
        item.status = status
        item.restocked = restock
        item.decision_note = note
        item.agreed_resolution = agreed_resolution
        item.agreed_amount = agreed_amount
        item.decided_at = timezone.now()
        item.save()
        if restock:
            _restock(item)
        _resolve_request_if_decided(item.return_request)
        _mark_order_returned_if_complete(item.return_request.order)
    return item


def _reason_allowed(item: OrderItem, reason: str) -> bool:
    return not (reason == ReturnReason.WITHDRAWAL and is_personalised(item))


def _validate_request(order: Order, reason: str, lines: list[ReturnLine]) -> None:
    if order.status != OrderStatus.DELIVERED or order.delivered_at is None:
        raise ValidationError(
            {
                "order": (
                    "Zwrot można zgłosić wyłącznie dla doręczonego zamówienia; "
                    "odstąpienie przed doręczeniem obsługuje sklep."
                )
            }
        )
    if reason not in ReturnReason.values:
        raise ValidationError({"reason": "Podstawa zwrotu jest obowiązkowa."})
    if timezone.now() > (deadline := return_deadline(order, reason)):
        raise ValidationError(
            {
                "reason": (
                    f"Termin na „{ReturnReason(reason).label}” minął "
                    f"{timezone.localtime(deadline):%Y-%m-%d %H:%M}."
                )
            }
        )
    if not lines:
        raise ValidationError({"items": "Zgłoszenie musi obejmować pozycję."})
    item_ids = [line.order_item.pk for line in lines]
    if len(set(item_ids)) != len(item_ids):
        raise ValidationError({"items": "Każda pozycja może wystąpić raz."})
    for line in lines:
        _validate_line(order, reason, line)


def _validate_line(order: Order, reason: str, line: ReturnLine) -> None:
    item = line.order_item
    if item.order_id != order.pk:  # type: ignore[missing-attribute]
        raise ValidationError({"items": "Pozycja nie należy do tego zamówienia."})
    left = returnable_quantity(item)
    if not 1 <= line.quantity <= left:
        raise ValidationError(
            {"items": f"Pozycję {item.sku} można zwrócić w ilości od 1 do {left}."}
        )
    if item.is_pair and line.quantity != item.quantity:
        raise ValidationError({"items": f"Para obrączek {item.sku} wraca w całości."})
    if not _reason_allowed(item, reason):
        raise ValidationError(
            {
                "reason": (
                    f"Odstąpienie nie obejmuje pozycji {item.sku} — wyrób "
                    "z grawerunkiem albo na zamówienie jest zindywidualizowany."
                )
            }
        )
    if reason == ReturnReason.COMPLAINT:
        if line.claim_request not in claim_requests_for(item):
            raise ValidationError(
                {
                    "items": (
                        f"Pozycja {item.sku}: wybierz żądanie reklamacyjne "
                        "dopuszczone przez produkt."
                    )
                }
            )
    elif line.claim_request:
        raise ValidationError(
            {"items": "Żądanie reklamacyjne wybiera się wyłącznie przy reklamacji."}
        )


def _restock(item: ReturnRequestItem) -> None:
    order_item = item.order_item
    inventory, _ = InventoryItem.objects.get_or_create(variant=order_item.variant)
    StockMovement.objects.create(
        item=inventory,
        quantity=item.quantity * order_item.specimen_count,
        reason=StockMovementReason.RETURN,
        note=(
            f"Zwrot {item.return_request_id}, zamówienie "  # type: ignore[missing-attribute]
            f"{order_item.order.number}"
        ),
    )


def _resolve_request_if_decided(request: ReturnRequest) -> None:
    if request.status == ReturnRequestStatus.RESOLVED:
        return
    if request.items.filter(status__in=OPEN_ITEM_STATUSES).exists():  # type: ignore[missing-attribute]
        return
    request.status = ReturnRequestStatus.RESOLVED
    request.save(update_fields=["status", "updated_at"])
    _notify(request)


def _mark_order_returned_if_complete(order: Order) -> None:
    """Zamówienie przechodzi w `returned`, gdy przyjęte zwroty objęły wszystko.

    Uwzględniona naprawa albo wymiana oddaje towar klientowi — to nie zwrot.
    """
    if not order.can_transition_to(OrderStatus.RETURNED):
        return
    accepted = dict(
        ReturnRequestItem.objects.filter(
            return_request__order=order, status=ReturnItemStatus.ACCEPTED
        )
        .exclude(claim_request__in=(ClaimRequest.REPAIR, ClaimRequest.REPLACEMENT))
        .values_list("order_item")
        .annotate(total=Sum("quantity"))
    )
    if all(accepted.get(item.pk, 0) >= item.quantity for item in order.items.all()):  # type: ignore[missing-attribute]
        order.transition_to(OrderStatus.RETURNED)


def _notify(request: ReturnRequest) -> None:
    """Transakcyjne powiadomienie o stanie zgłoszenia, po zatwierdzeniu zapisu."""
    order = request.order
    payload = {
        "order_number": order.number,
        "return_request_id": str(request.pk),
        "status_label": request.get_status_display(),  # type: ignore[missing-attribute]
    }
    # Jak w `orders/signals.py`: rekord na konto, e-mail na kopię z zamówienia.
    recipient = order.user if order.user_id is not None else order.email  # type: ignore[missing-attribute]
    transaction.on_commit(
        lambda: notify(
            recipient,  # type: ignore[bad-argument-type]
            NotificationKind.RETURN_REQUEST_STATUS_CHANGED,
            payload,
            email=order.email,
        ),
        robust=True,
    )
