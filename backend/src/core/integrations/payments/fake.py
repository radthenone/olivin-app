from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from typing import ClassVar

from core.integrations.payments.base import (
    EventKind,
    Intent,
    InvalidSignature,
    PaymentProviderError,
    ProviderEvent,
)

FAKE_WEBHOOK_SECRET = "fake-webhook-secret"


class FakePaymentProvider:
    """Atrapa operatora płatności do testów i pracy bez klucza (ADR 0027).

    Zapamiętuje założone intencje i zwroty na poziomie klasy, bo rejestr
    tworzy nowy obiekt przy każdym wywołaniu — test zagląda do tych list
    zamiast podsłuchiwać sieć. Zdarzenie podpisuje zwykłym HMAC, więc ścieżka
    weryfikacji podpisu jest sprawdzana naprawdę, a nie pomijana.
    """

    signature_header = "Fake-Signature"

    intents: ClassVar[list[dict]] = []
    refunds: ClassVar[list[dict]] = []
    # Ustawione na komunikat — następne wywołanie operatora odmówi.
    fail_with: ClassVar[str] = ""

    @classmethod
    def reset(cls) -> None:
        cls.intents = []
        cls.refunds = []
        cls.fail_with = ""

    def create_intent(
        self,
        *,
        amount: int,
        currency: str,
        reference: str,
        idempotency_key: str,
    ) -> Intent:
        self._fail_if_requested()
        for existing in self.intents:
            if existing["idempotency_key"] == idempotency_key:
                return Intent(id=existing["id"], client_secret=existing["secret"])
        intent_id = f"pi_fake_{secrets.token_hex(8)}"
        secret = f"{intent_id}_secret_{secrets.token_hex(8)}"
        self.intents.append(
            {
                "id": intent_id,
                "secret": secret,
                "amount": amount,
                "currency": currency,
                "reference": reference,
                "idempotency_key": idempotency_key,
            }
        )
        return Intent(id=intent_id, client_secret=secret)

    def refund(
        self, intent_id: str, *, idempotency_key: str, amount: int | None = None
    ) -> str:
        self._fail_if_requested()
        for existing in self.refunds:
            if existing["idempotency_key"] == idempotency_key:
                return existing["id"]
        refund_id = f"re_fake_{secrets.token_hex(8)}"
        self.refunds.append(
            {
                "id": refund_id,
                "intent_id": intent_id,
                "idempotency_key": idempotency_key,
                "amount": amount,
            }
        )
        return refund_id

    def verify_signature(self, payload: bytes, signature: str) -> ProviderEvent:
        if not hmac.compare_digest(sign(payload), signature or ""):
            raise InvalidSignature("Podpis zdarzenia nie zgadza się z treścią.")
        data = json.loads(payload)
        return ProviderEvent(
            id=data["id"],
            kind=EventKind(data["kind"]),
            type=data["kind"],
            intent_id=data.get("intent_id", ""),
            refund_id=data.get("refund_id", ""),
            payload=data,
        )

    def _fail_if_requested(self) -> None:
        if self.fail_with:
            raise PaymentProviderError(self.fail_with)


def sign(payload: bytes) -> str:
    """Podpis, którym atrapa „operatora” opatruje zdarzenie."""
    return hmac.new(FAKE_WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()


def event_payload(
    kind: EventKind, intent_id: str, event_id: str = "", refund_id: str = ""
) -> bytes:
    """Treść zdarzenia atrapy — tak, jak przyszłaby w ciele żądania."""
    return json.dumps(
        {
            "id": event_id or f"evt_fake_{secrets.token_hex(8)}",
            "kind": str(kind),
            "intent_id": intent_id,
            "refund_id": refund_id,
        }
    ).encode()
