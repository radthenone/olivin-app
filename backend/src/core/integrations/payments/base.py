from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol


class InvalidSignature(Exception):
    """Zdarzenie bez ważnego podpisu operatora — nie wolno go przetworzyć."""


class PaymentProviderError(Exception):
    """Operator odmówił albo nie odpowiedział — klient może spróbować ponownie."""


class PaymentProviderDeclined(PaymentProviderError):
    """Jednoznaczna odmowa operatora — ponowienie tym samym zleceniem nic nie da.

    Odróżnia „nie” od „nie wiadomo”: po przekroczeniu czasu operator mógł
    zlecenie wykonać, więc sklep nie może wtedy założyć, że pieniądze nie wyszły.
    """


class EventKind(StrEnum):
    """Rodzaj zdarzenia operatora sprowadzony do tego, co sklep rozróżnia.

    Nazwy zdarzeń operatora zostają w adapterze (ADR 0027): serwis płatności
    reaguje na „zapłacono”, a nie na `payment_intent.succeeded`.
    """

    PAYMENT_SUCCEEDED = "payment_succeeded"
    PAYMENT_FAILED = "payment_failed"
    REFUNDED = "refunded"
    REFUND_FAILED = "refund_failed"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class Intent:
    """Intencja płatnicza założona u operatora."""

    id: str
    client_secret: str


@dataclass(frozen=True, slots=True)
class ProviderEvent:
    """Zweryfikowane zdarzenie operatora.

    `intent_id` jest pusty przy zdarzeniach, które nie dotyczą żadnej
    intencji — te sklep zapisuje i pomija. `refund_id` niosą zdarzenia
    zwrotu: odróżnia częściowy zwrot za zgłoszenie od zwrotu całej płatności.
    """

    id: str
    kind: EventKind
    type: str
    intent_id: str = ""
    refund_id: str = ""
    metadata: dict = field(default_factory=dict)
    payload: dict = field(default_factory=dict)


class PaymentProvider(Protocol):
    """Operator płatności (ADR 0012, ADR 0027).

    Kwota zawsze w najmniejszej jednostce waluty (ADR 0009) — tak samo
    liczy ją operator, więc przez granicę nie przechodzi żaden ułamek.
    """

    # Nagłówek HTTP, w którym operator przesyła podpis zdarzenia.
    signature_header: str

    def create_intent(
        self,
        *,
        amount: int,
        currency: str,
        reference: str,
        idempotency_key: str,
    ) -> Intent: ...

    def refund(
        self,
        intent_id: str,
        *,
        idempotency_key: str,
        amount: int | None = None,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Zleca zwrot; bez `amount` — całej płatności, z nim — części.

        `metadata` wraca w zdarzeniach zwrotu — pozwala rozpoznać zwrot, którego
        identyfikatora sklep nie zdążył zapisać.
        """
        ...

    def verify_signature(self, payload: bytes, signature: str) -> ProviderEvent: ...
