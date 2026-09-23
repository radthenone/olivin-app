from __future__ import annotations

import stripe
from django.conf import settings

from core.integrations.payments.base import (
    EventKind,
    Intent,
    InvalidSignature,
    PaymentProviderError,
    ProviderEvent,
)

# Zdarzenia Stripe, na które sklep reaguje; pozostałe zapisuje i pomija.
_EVENT_KINDS = {
    "payment_intent.succeeded": EventKind.PAYMENT_SUCCEEDED,
    "payment_intent.payment_failed": EventKind.PAYMENT_FAILED,
    "refund.failed": EventKind.REFUND_FAILED,
}

# Zwrot kończy się dopiero stanem `succeeded` na obiekcie zwrotu. Nie
# `charge.refunded`: to przychodzi już przy zleceniu, także gdy zwrot przez
# Przelewy24 czy BLIK dopiero czeka — zamówienie anulowałoby się, zanim
# pieniądze faktycznie wróciły.
_REFUND_EVENTS = {"refund.created", "refund.updated"}
_REFUND_STATUS_KINDS = {
    "succeeded": EventKind.REFUNDED,
    "failed": EventKind.REFUND_FAILED,
}


class StripeProvider:
    """Stripe przez Payment Intents — dostawca produkcyjny (ADR 0012).

    Metody płatności (karta, BLIK, Przelewy24) i Radar konfiguruje się
    w panelu Stripe: `automatic_payment_methods` bierze to, co tam włączono,
    więc nowa metoda nie wymaga zmiany kodu.
    """

    signature_header = "Stripe-Signature"

    def __init__(
        self, api_key: str | None = None, webhook_secret: str | None = None
    ) -> None:
        self.api_key = api_key or getattr(settings, "STRIPE_SECRET_KEY", "")
        self.webhook_secret = webhook_secret or getattr(
            settings, "STRIPE_WEBHOOK_SECRET", ""
        )

    def create_intent(
        self,
        *,
        amount: int,
        currency: str,
        reference: str,
        idempotency_key: str,
    ) -> Intent:
        try:
            intent = self._client().v1.payment_intents.create(
                params={
                    "amount": amount,
                    "currency": currency.lower(),
                    "automatic_payment_methods": {"enabled": True},
                    "metadata": {"order": reference},
                },
                options={"idempotency_key": idempotency_key},
            )
        except stripe.StripeError as error:
            raise PaymentProviderError(str(error)) from error
        return Intent(id=intent.id, client_secret=intent.client_secret or "")

    def refund(self, intent_id: str, *, idempotency_key: str) -> str:
        try:
            refund = self._client().v1.refunds.create(
                params={"payment_intent": intent_id},
                options={"idempotency_key": idempotency_key},
            )
        except stripe.StripeError as error:
            raise PaymentProviderError(str(error)) from error
        return refund.id

    def verify_signature(self, payload: bytes, signature: str) -> ProviderEvent:
        if not self.webhook_secret:
            raise RuntimeError(
                "Brak sekretu zdarzeń Stripe — ustaw STRIPE_WEBHOOK_SECRET."
            )
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
        except (stripe.SignatureVerificationError, ValueError) as error:
            raise InvalidSignature(str(error)) from error

        data = event.to_dict()
        obj = data.get("data", {}).get("object", {})
        kind = _EVENT_KINDS.get(event.type, EventKind.OTHER)
        if event.type in _REFUND_EVENTS:
            kind = _REFUND_STATUS_KINDS.get(obj.get("status", ""), EventKind.OTHER)
        return ProviderEvent(
            id=event.id,
            kind=kind,
            type=event.type,
            intent_id=_intent_id_of(obj),
            payload=data,
        )

    def _client(self) -> stripe.StripeClient:
        if not self.api_key:
            raise RuntimeError(
                "Brak klucza Stripe — ustaw STRIPE_SECRET_KEY albo wybierz innego "
                "dostawcę przez PAYMENT_PROVIDER."
            )
        return stripe.StripeClient(self.api_key)


def _intent_id_of(obj: dict) -> str:
    """Identyfikator intencji z obiektu zdarzenia.

    Zdarzenie intencji niesie ją jako obiekt główny; zdarzenia obciążenia
    i zwrotu wskazują ją polem `payment_intent`.
    """
    if obj.get("object") == "payment_intent":
        return obj.get("id", "")
    return obj.get("payment_intent") or ""
