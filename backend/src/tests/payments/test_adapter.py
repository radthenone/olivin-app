"""Adapter operatora płatności (ADR 0027) — bez sieci."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from unittest.mock import MagicMock, patch

import pytest

from core.integrations.payments import (
    EventKind,
    InvalidSignature,
    PaymentProviderDeclined,
    PaymentProviderError,
    get_provider,
)
from core.integrations.payments.fake import FakePaymentProvider, event_payload, sign
from core.integrations.payments.stripe import StripeProvider

SECRET = "whsec_test"


def _stripe_signature(payload: bytes, secret: str = SECRET) -> str:
    """Nagłówek podpisu w formacie Stripe: znacznik czasu i HMAC-SHA256."""
    timestamp = int(time.time())
    signed = f"{timestamp}.{payload.decode()}".encode()
    digest = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


def _stripe_event(event_type: str, obj: dict) -> bytes:
    return json.dumps(
        {
            "id": "evt_1",
            "object": "event",
            "type": event_type,
            "data": {"object": obj},
        }
    ).encode()


class TestStripe:
    def test_sukces_intencji_jest_zapisany_po_naszemu(self):
        payload = _stripe_event(
            "payment_intent.succeeded", {"id": "pi_1", "object": "payment_intent"}
        )

        event = StripeProvider("sk_test", SECRET).verify_signature(
            payload, _stripe_signature(payload)
        )

        assert event.id == "evt_1"
        assert event.kind == EventKind.PAYMENT_SUCCEEDED
        assert event.intent_id == "pi_1"

    @pytest.mark.parametrize(
        ("event_type", "refund_status", "kind"),
        [
            ("refund.created", "succeeded", EventKind.REFUNDED),
            ("refund.updated", "succeeded", EventKind.REFUNDED),
            ("refund.created", "pending", EventKind.OTHER),
            ("refund.updated", "failed", EventKind.REFUND_FAILED),
            ("refund.updated", "canceled", EventKind.REFUND_FAILED),
        ],
    )
    def test_zwrot_konczy_dopiero_status_succeeded(
        self, event_type, refund_status, kind
    ):
        payload = _stripe_event(
            event_type,
            {
                "id": "re_1",
                "object": "refund",
                "status": refund_status,
                "payment_intent": "pi_1",
                "metadata": {"return_request_id": "rr_1"},
            },
        )

        event = StripeProvider("sk_test", SECRET).verify_signature(
            payload, _stripe_signature(payload)
        )

        assert event.kind == kind
        assert event.intent_id == "pi_1"
        assert event.refund_id == "re_1"
        assert event.metadata == {"return_request_id": "rr_1"}

    def test_charge_refunded_nie_konczy_zwrotu(self):
        payload = _stripe_event(
            "charge.refunded",
            {"id": "ch_1", "object": "charge", "payment_intent": "pi_1"},
        )

        event = StripeProvider("sk_test", SECRET).verify_signature(
            payload, _stripe_signature(payload)
        )

        assert event.kind == EventKind.OTHER

    def test_nieznane_zdarzenie_to_other(self):
        payload = _stripe_event("customer.created", {"id": "cus_1"})

        event = StripeProvider("sk_test", SECRET).verify_signature(
            payload, _stripe_signature(payload)
        )

        assert event.kind == EventKind.OTHER
        assert event.intent_id == ""

    def test_podpis_innym_sekretem_jest_odrzucony(self):
        payload = _stripe_event("payment_intent.succeeded", {"id": "pi_1"})

        with pytest.raises(InvalidSignature):
            StripeProvider("sk_test", SECRET).verify_signature(
                payload, _stripe_signature(payload, secret="whsec_obcy")
            )

    def test_zmieniona_tresc_jest_odrzucona(self):
        payload = _stripe_event("payment_intent.succeeded", {"id": "pi_1"})
        signature = _stripe_signature(payload)

        with pytest.raises(InvalidSignature):
            StripeProvider("sk_test", SECRET).verify_signature(
                payload.replace(b"pi_1", b"pi_2"), signature
            )

    def test_intencja_idzie_z_kluczem_idempotencji(self):
        client = MagicMock()
        client.v1.payment_intents.create.return_value = MagicMock(
            id="pi_1", client_secret="pi_1_secret"
        )

        with patch("stripe.StripeClient", return_value=client):
            intent = StripeProvider("sk_test", SECRET).create_intent(
                amount=101990,
                currency="PLN",
                reference="ABC",
                idempotency_key="order-ABC-payment-1",
            )

        assert intent.client_secret == "pi_1_secret"
        kwargs = client.v1.payment_intents.create.call_args.kwargs
        assert kwargs["params"]["amount"] == 101990
        assert kwargs["params"]["currency"] == "pln"
        assert kwargs["options"] == {"idempotency_key": "order-ABC-payment-1"}

    def test_blad_stripe_to_blad_operatora(self):
        import stripe

        client = MagicMock()
        client.v1.refunds.create.side_effect = stripe.APIConnectionError("down")

        with patch("stripe.StripeClient", return_value=client):
            with pytest.raises(PaymentProviderError):
                StripeProvider("sk_test", SECRET).refund(
                    "pi_1", idempotency_key="refund-pi_1"
                )

    def test_card_error_is_unambiguous_decline(self):
        """Odrzucenie przez bank to „nie”, nie „nie wiadomo” — bez ponawiania."""
        import stripe

        client = MagicMock()
        client.v1.refunds.create.side_effect = stripe.CardError(
            "card closed", None, "card_declined"
        )

        with patch("stripe.StripeClient", return_value=client):
            with pytest.raises(PaymentProviderDeclined):
                StripeProvider("sk_test", SECRET).refund(
                    "pi_1", idempotency_key="refund-pi_1"
                )

    def test_connection_error_is_not_a_decline(self):
        """Brak odpowiedzi mógł nastąpić po wykonaniu zwrotu — to nie odmowa."""
        import stripe

        client = MagicMock()
        client.v1.refunds.create.side_effect = stripe.APIConnectionError("down")

        with patch("stripe.StripeClient", return_value=client):
            with pytest.raises(PaymentProviderError) as raised:
                StripeProvider("sk_test", SECRET).refund(
                    "pi_1", idempotency_key="refund-pi_1"
                )
        assert not isinstance(raised.value, PaymentProviderDeclined)

    def test_partial_refund_sends_amount_and_metadata(self):
        """Zwrot za zgłoszenie idzie z kwotą i identyfikatorem zgłoszenia."""
        client = MagicMock()
        client.v1.refunds.create.return_value = MagicMock(id="re_1")

        with patch("stripe.StripeClient", return_value=client):
            StripeProvider("sk_test", SECRET).refund(
                "pi_1",
                idempotency_key="return-1-refund",
                amount=5000,
                metadata={"return_request_id": "1"},
            )

        params = client.v1.refunds.create.call_args.kwargs["params"]
        assert params == {
            "payment_intent": "pi_1",
            "amount": 5000,
            "metadata": {"return_request_id": "1"},
        }


class TestAtrapa:
    def test_rejestr_zwraca_atrape_w_testach(self):
        assert isinstance(get_provider(), FakePaymentProvider)

    def test_podpis_atrapy_przechodzi(self):
        payload = event_payload(EventKind.PAYMENT_FAILED, "pi_1", "evt_1")

        event = FakePaymentProvider().verify_signature(payload, sign(payload))

        assert event.kind == EventKind.PAYMENT_FAILED
        assert event.intent_id == "pi_1"

    def test_ten_sam_klucz_idempotencji_to_ta_sama_intencja(self):
        provider = FakePaymentProvider()

        first = provider.create_intent(
            amount=100, currency="PLN", reference="A", idempotency_key="k"
        )
        second = provider.create_intent(
            amount=100, currency="PLN", reference="A", idempotency_key="k"
        )

        assert first == second
