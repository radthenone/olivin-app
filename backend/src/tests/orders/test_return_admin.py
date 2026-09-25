"""Panel zgłoszeń zwrotu — decyzja per pozycja przez serwis (#196)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from freezegun import freeze_time

from apps.inventory.models import StockMovement, StockMovementReason
from apps.orders.models import OrderStatus, ReturnItemStatus, ReturnReason
from apps.orders.services.returns import (
    ReturnLine,
    create_return_request,
    decide_return_item,
)
from tests.factories.orders import OrderFactory, OrderItemFactory
from tests.factories.products import stock


def _goodwill_request(*quantities: int):
    with freeze_time("2027-03-01 12:00:00+01:00"):
        order = OrderFactory(status=OrderStatus.DELIVERED)
    items = [OrderItemFactory(order=order, quantity=q) for q in quantities]
    with freeze_time("2027-03-02"):
        request = create_return_request(
            order,
            reason=ReturnReason.GOODWILL,
            lines=[ReturnLine(item, item.quantity) for item in items],
        )
    return request


def _post(admin_client, request, rows: list[dict], **kwargs):
    data = {
        "items-TOTAL_FORMS": str(len(rows)),
        "items-INITIAL_FORMS": str(len(rows)),
        "items-MIN_NUM_FORMS": "0",
        "items-MAX_NUM_FORMS": "1000",
    }
    for index, (item, row) in enumerate(
        zip(request.items.order_by("created_at", "id"), rows, strict=True)
    ):
        data[f"items-{index}-id"] = str(item.pk)
        data[f"items-{index}-return_request"] = str(request.pk)
        data.update({f"items-{index}-{key}": value for key, value in row.items()})
    url = reverse("admin:orders_returnrequest_change", args=[request.pk])
    return admin_client.post(url, data, **kwargs)


@pytest.mark.django_db
class TestReturnRequestAdmin:
    """Obsługa rozstrzyga pozycje w panelu."""

    def test_admin_accepts_one_item_back_in_stock_and_rejects_other(self, admin_client):
        """Przyjęcie z powrotem na stan i odrzucenie z uzasadnieniem naraz."""
        request = _goodwill_request(1, 1)
        first, second = request.items.order_by("created_at", "id")
        stock(first.order_item.variant, 3)

        response = _post(
            admin_client,
            request,
            [
                {"decision": ReturnItemStatus.ACCEPTED, "restocked": "on"},
                {"decision": ReturnItemStatus.REJECTED, "decision_note": "Ślady"},
            ],
        )

        assert response.status_code == 302
        first.refresh_from_db()
        second.refresh_from_db()
        assert first.status == ReturnItemStatus.ACCEPTED
        assert second.status == ReturnItemStatus.REJECTED
        assert (
            StockMovement.objects.filter(reason=StockMovementReason.RETURN).count() == 1
        )

    def test_rejection_without_note_shows_form_error(self, admin_client):
        """Błąd reguły wraca jako komunikat formularza, nie błąd serwera."""
        request = _goodwill_request(1)

        response = _post(
            admin_client, request, [{"decision": ReturnItemStatus.REJECTED}]
        )

        assert response.status_code == 200
        assert "uzasadnienia" in response.content.decode()
        assert request.items.get().status == ReturnItemStatus.PENDING

    def test_row_without_decision_stays_untouched(self, admin_client):
        """Wiersz bez decyzji nie zmienia się — nawet jego notatka."""
        request = _goodwill_request(1)

        response = _post(admin_client, request, [{"decision_note": "Notatka"}])

        assert response.status_code == 302
        item = request.items.get()
        assert item.status == ReturnItemStatus.PENDING
        assert item.decision_note == ""

    def test_decided_row_is_read_only(self, admin_client):
        """Rozstrzygnięta pozycja nie przyjmuje nowej decyzji ani ruchu na stan."""
        request = _goodwill_request(1, 1)
        first = request.items.order_by("created_at", "id").first()
        assert first is not None
        stock(first.order_item.variant, 3)
        decide_return_item(first, status=ReturnItemStatus.ACCEPTED)

        response = _post(
            admin_client,
            request,
            [
                {"decision": ReturnItemStatus.ACCEPTED, "restocked": "on"},
                {},
            ],
        )

        assert response.status_code == 302
        first.refresh_from_db()
        assert not first.restocked
        assert not StockMovement.objects.filter(
            reason=StockMovementReason.RETURN
        ).exists()

    def test_rule_broken_at_save_shows_message_not_500(self, admin_client):
        """Reguła złamana dopiero przy zapisie (np. równoległa decyzja) to komunikat."""
        request = _goodwill_request(1)

        with patch(
            "apps.orders.admin.decide_return_item",
            side_effect=ValidationError({"status": "Pozycja jest już rozstrzygnięta."}),
        ):
            response = _post(
                admin_client,
                request,
                [{"decision": ReturnItemStatus.ACCEPTED}],
                follow=True,
            )

        assert response.status_code == 200
        assert "już rozstrzygnięta" in response.content.decode()
