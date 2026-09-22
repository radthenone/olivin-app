from __future__ import annotations

from rest_framework import serializers

from apps.payments.models import PaymentStatus
from core.api.serializers import MoneySerializer


class PaymentIntentSerializer(serializers.Serializer):
    """Rozpoczęta zapłata (`StartedPayment`): sekret i kwota intencji.

    Sekret otwiera komponent płatności u klienta (ADR 0012) — nie jest
    kluczem do konta sklepu i nie pozwala niczego obciążyć bez klienta.
    Kwota wraca, żeby klient pokazał dokładnie tę, którą obciąży operator.
    """

    id = serializers.IntegerField(source="payment.id", read_only=True)
    status = serializers.ChoiceField(
        source="payment.status", choices=PaymentStatus.choices, read_only=True
    )
    amount = MoneySerializer(source="payment.amount_money", read_only=True)
    client_secret = serializers.CharField(
        read_only=True,
        help_text="Sekret intencji dla arkusza płatności (mobile) i elementu (web)",
    )


class WebhookAckSerializer(serializers.Serializer):
    """Potwierdzenie odbioru zdarzenia; `processed` fałszywe przy powtórce."""

    processed = serializers.BooleanField(read_only=True)
