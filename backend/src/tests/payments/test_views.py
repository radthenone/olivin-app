"""API zapłaty i webhook operatora na realnym kształcie odpowiedzi."""

from __future__ import annotations

from typing import Any

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser
from apps.orders.models import OrderStatus
from apps.payments.models import Payment, PaymentStatus, WebhookEvent
from apps.payments.services import start_payment
from core.integrations.payments import EventKind
from tests.factories.accounts import UserFactory
from tests.payments.helpers import placed_order, signed_event

SIGNATURE_HEADER = "HTTP_FAKE_SIGNATURE"


def _payment_url(number: str) -> str:
    return reverse("order-payment", args=[number])


def _cancel_url(number: str) -> str:
    return reverse("order-cancel", args=[number])


def _webhook(client: APIClient, payload: bytes, signature: str) -> Any:
    return client.post(
        reverse("payment-webhook"),
        data=payload,
        content_type="application/json",
        **{SIGNATURE_HEADER: signature},
    )


@pytest.mark.django_db
class TestStartPayment:
    """Rozpoczęcie zapłaty przez API."""

    def test_returns_secret_and_amount(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        """Odpowiedź zawiera sekret i kwotę."""
        order = placed_order(user=user)

        response: Any = authenticated_client.post(_payment_url(order.number))

        body = response.json()
        assert response.status_code == status.HTTP_201_CREATED
        assert body["clientSecret"]
        assert body["amount"] == {"amount": order.total.amount, "currency": "PLN"}
        assert body["status"] == PaymentStatus.PENDING
        assert Payment.objects.filter(pk=body["id"], order=order).exists()

    def test_other_customer_order_is_404(self, authenticated_client: APIClient):
        """Cudze zamówienie daje 404."""
        order = placed_order(user=UserFactory())

        response: Any = authenticated_client.post(_payment_url(order.number))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cancelled_order_is_400(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        """Anulowane zamówienie daje 400."""
        order = placed_order(user=user)
        authenticated_client.post(_cancel_url(order.number))

        response: Any = authenticated_client.post(_payment_url(order.number))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "status" in response.data


@pytest.mark.django_db
class TestWebhook:
    """Webhook operatora płatności."""

    def test_signed_event_pays_order(
        self, api_client: APIClient, authenticated_client: APIClient, user
    ):
        """Podpisane zdarzenie opłaca zamówienie."""
        order = placed_order(user=user)
        started: Any = authenticated_client.post(_payment_url(order.number))
        intent_id = Payment.objects.get(pk=started.data["id"]).intent_id
        payload, signature = signed_event(EventKind.PAYMENT_SUCCEEDED, intent_id)

        response: Any = _webhook(api_client, payload, signature)

        order.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"processed": True}
        assert order.status == OrderStatus.PAID

    def test_repeated_event_changes_nothing(self, api_client: APIClient):
        """Powtórka zdarzenia niczego nie zmienia."""
        order = placed_order()
        intent_id = start_payment(order).payment.intent_id
        payload, signature = signed_event(
            EventKind.PAYMENT_SUCCEEDED, intent_id, "evt_same"
        )

        first: Any = _webhook(api_client, payload, signature)
        second: Any = _webhook(api_client, payload, signature)

        assert first.data == {"processed": True}
        assert second.status_code == status.HTTP_200_OK
        assert second.data == {"processed": False}
        assert WebhookEvent.objects.count() == 1

    def test_bad_signature_is_400_without_record(self, api_client: APIClient):
        """Zły podpis daje 400 i nic nie zapisuje."""
        order = placed_order()
        intent_id = start_payment(order).payment.intent_id
        payload, _ = signed_event(EventKind.PAYMENT_SUCCEEDED, intent_id)

        response: Any = _webhook(api_client, payload, "podrobiony")

        order.refresh_from_db()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert order.status == OrderStatus.PENDING
        assert not WebhookEvent.objects.exists()

    def test_missing_signature_is_400(self, api_client: APIClient):
        """Brak podpisu daje 400."""
        payload, _ = signed_event(EventKind.PAYMENT_SUCCEEDED, "pi_x")

        response: Any = api_client.post(
            reverse("payment-webhook"), data=payload, content_type="application/json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCancelPaidOrder:
    """Anulowanie opłaconego zamówienia przez API."""

    def test_cancelling_paid_returns_202_and_waits_for_refund(
        self, api_client: APIClient, authenticated_client: APIClient, user
    ):
        """Anulowanie opłaconego odpowiada 202 i czeka na zwrot."""
        order = placed_order(user=user)
        started: Any = authenticated_client.post(_payment_url(order.number))
        intent_id = Payment.objects.get(pk=started.data["id"]).intent_id
        _webhook(api_client, *signed_event(EventKind.PAYMENT_SUCCEEDED, intent_id))

        response: Any = authenticated_client.post(_cancel_url(order.number))

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data["status"] == OrderStatus.PAID

        _webhook(api_client, *signed_event(EventKind.REFUNDED, intent_id))

        order.refresh_from_db()
        assert order.status == OrderStatus.CANCELLED

    def test_cancelling_pending_is_still_immediate(
        self, authenticated_client: APIClient, user
    ):
        """Anulowanie `pending` dalej działa od razu."""
        order = placed_order(user=user)

        response: Any = authenticated_client.post(_cancel_url(order.number))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == OrderStatus.CANCELLED
