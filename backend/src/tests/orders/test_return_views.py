"""API zgłoszeń zwrotu — klient i gość tą samą drogą co zamówienie (#196)."""

from __future__ import annotations

from typing import Any

import pytest
from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser
from apps.orders.models import (
    ClaimRequest,
    OrderStatus,
    ReturnItemStatus,
    ReturnReason,
    ReturnRequest,
)
from tests.factories.orders import GuestOrderFactory, OrderFactory, OrderItemFactory
from tests.factories.products import ProductFactory, ProductVariantFactory

DELIVERED = "2027-03-01 12:00:00+01:00"
LATER = "2027-03-05 12:00:00+01:00"


def _options_url(number: str) -> str:
    return reverse("order-return-options", args=[number])


def _returns_url(number: str) -> str:
    return reverse("order-returns", args=[number])


def _return_url(number: str, pk) -> str:
    return reverse("order-return-detail", args=[number, pk])


def _delivered(factory=OrderFactory, **kwargs):
    with freeze_time(DELIVERED):
        return factory(status=OrderStatus.DELIVERED, **kwargs)


@pytest.mark.django_db
class TestReturnOptionsApi:
    """Formularz zwrotu: co, z jakiej podstawy i do kiedy."""

    def test_options_list_items_reasons_deadlines_and_claims(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        """Pozycja z terminami otwartych podstaw i dostępnymi żądaniami."""
        order = _delivered(user=user)
        product = ProductFactory(replacement_available=True)
        item = OrderItemFactory(
            order=order, variant=ProductVariantFactory(product=product), quantity=2
        )

        with freeze_time(LATER):
            response: Any = authenticated_client.get(_options_url(order.number))

        assert response.status_code == status.HTTP_200_OK
        [option] = response.json()
        assert option["orderItem"] == str(item.pk)
        assert option["returnableQuantity"] == 2
        assert option["claimRequests"] == ["refund", "replacement"]
        reasons = {row["reason"]: row["deadline"] for row in option["deadlines"]}
        assert set(reasons) == {"withdrawal", "goodwill", "complaint"}
        assert reasons["withdrawal"].startswith("2027-03-15")


@pytest.mark.django_db
class TestCreateReturnRequestApi:
    """Złożenie zgłoszenia."""

    def test_customer_creates_request(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        """Zalogowany klient zgłasza zwrot pozycji własnego zamówienia."""
        order = _delivered(user=user)
        item = OrderItemFactory(order=order)

        with freeze_time(LATER):
            response: Any = authenticated_client.post(
                _returns_url(order.number),
                {
                    "reason": "complaint",
                    "items": [
                        {
                            "orderItem": str(item.pk),
                            "quantity": 1,
                            "claimRequest": "refund",
                        }
                    ],
                },
                format="json",
            )

        assert response.status_code == status.HTTP_201_CREATED, response.json()
        body = response.json()
        assert body["reason"] == "complaint"
        assert body["status"] == "submitted"
        assert body["items"][0]["status"] == "pending"
        assert body["items"][0]["claimRequest"] == "refund"
        assert ReturnRequest.objects.filter(order=order).count() == 1

    def test_rule_violation_is_400(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        """Odstąpienie od grawerowanej pozycji wraca jako błąd walidacji."""
        order = _delivered(user=user)
        item = OrderItemFactory(
            order=order, engraving_text="Na zawsze", engraving_price=5000
        )

        with freeze_time(LATER):
            response: Any = authenticated_client.post(
                _returns_url(order.number),
                {
                    "reason": "withdrawal",
                    "items": [{"orderItem": str(item.pk), "quantity": 1}],
                },
                format="json",
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not ReturnRequest.objects.exists()

    def test_missing_reason_is_400(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        """Podstawa jest obowiązkowa już na poziomie kontraktu."""
        order = _delivered(user=user)
        item = OrderItemFactory(order=order)

        response: Any = authenticated_client.post(
            _returns_url(order.number),
            {"items": [{"orderItem": str(item.pk), "quantity": 1}]},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "reason" in response.json()

    def test_foreign_order_is_404(self, authenticated_client: APIClient):
        """Cudze zamówienie nie istnieje dla klienta."""
        order = _delivered()
        item = OrderItemFactory(order=order)

        with freeze_time(LATER):
            response: Any = authenticated_client.post(
                _returns_url(order.number),
                {
                    "reason": "goodwill",
                    "items": [{"orderItem": str(item.pk), "quantity": 1}],
                },
                format="json",
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_guest_creates_request_with_order_email(self, api_client: APIClient):
        """Gość zgłasza zwrot numerem zamówienia i adresem e-mail."""
        order = _delivered(GuestOrderFactory)
        item = OrderItemFactory(order=order)
        url = f"{_returns_url(order.number)}?email={order.email}"

        with freeze_time(LATER):
            response: Any = api_client.post(
                url,
                {
                    "reason": "goodwill",
                    "items": [{"orderItem": str(item.pk), "quantity": 1}],
                },
                format="json",
            )

        assert response.status_code == status.HTTP_201_CREATED, response.json()

    def test_guest_without_email_is_404(self, api_client: APIClient):
        """Sam numer zamówienia nie otwiera zwrotów gościa."""
        order = _delivered(GuestOrderFactory)
        item = OrderItemFactory(order=order)

        response: Any = api_client.post(
            _returns_url(order.number),
            {
                "reason": "goodwill",
                "items": [{"orderItem": str(item.pk), "quantity": 1}],
            },
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestReadReturnRequestsApi:
    """Lista i szczegóły własnych zgłoszeń."""

    def _request(self, order):
        item = OrderItemFactory(order=order)
        request = ReturnRequest.objects.create(
            order=order, reason=ReturnReason.COMPLAINT
        )
        request.items.create(
            order_item=item,
            quantity=1,
            claim_request=ClaimRequest.REFUND,
            status=ReturnItemStatus.REJECTED,
            decision_note="Uszkodzenie mechaniczne",
        )
        return request

    def test_customer_lists_and_reads_own_requests(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        """Lista zgłoszeń zamówienia i szczegół z uzasadnieniem decyzji."""
        order = _delivered(user=user)
        request = self._request(order)
        self._request(_delivered())

        listed: Any = authenticated_client.get(_returns_url(order.number))
        detail: Any = authenticated_client.get(_return_url(order.number, request.pk))

        assert listed.status_code == status.HTTP_200_OK
        assert [row["id"] for row in listed.json()] == [str(request.pk)]
        assert detail.status_code == status.HTTP_200_OK
        assert detail.json()["items"][0]["decisionNote"] == "Uszkodzenie mechaniczne"

    def test_request_of_other_order_is_404(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        """Zgłoszenie czytane wyłącznie przez swoje zamówienie."""
        order = _delivered(user=user)
        foreign = self._request(_delivered())

        response: Any = authenticated_client.get(_return_url(order.number, foreign.pk))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_guest_reads_requests_with_email(self, api_client: APIClient):
        """Gość czyta zgłoszenia tą samą parą numer + e-mail."""
        order = _delivered(GuestOrderFactory)
        request = self._request(order)

        response: Any = api_client.get(
            f"{_return_url(order.number, request.pk)}?email={order.email}"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["reason"] == "complaint"
