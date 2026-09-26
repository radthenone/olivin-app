from __future__ import annotations

from rest_framework import serializers

from apps.orders.models import (
    ClaimRequest,
    ReturnReason,
    ReturnRequest,
    ReturnRequestItem,
)
from core.api.serializers import MoneySerializer


class ReturnDeadlineSerializer(serializers.Serializer):
    """Otwarta podstawa zwrotu i chwila, do której można z niej skorzystać."""

    reason = serializers.ChoiceField(choices=ReturnReason.choices, read_only=True)
    deadline = serializers.DateTimeField(read_only=True)


class ReturnOptionSerializer(serializers.Serializer):
    """Pozycja w formularzu zwrotu: co, z jakiej podstawy, do kiedy."""

    order_item = serializers.UUIDField(source="item.pk", read_only=True)
    product_name = serializers.CharField(source="item.product_name", read_only=True)
    sku = serializers.CharField(source="item.sku", read_only=True)
    is_pair = serializers.BooleanField(
        source="item.is_pair",
        read_only=True,
        help_text="Para obrączek wraca w całości — ilość równa kupionej",
    )
    returnable_quantity = serializers.IntegerField(
        read_only=True,
        help_text="Ilość nieobjęta żadnym nieodrzuconym zgłoszeniem",
    )
    deadlines = ReturnDeadlineSerializer(
        source="deadline_rows",
        many=True,
        read_only=True,
        help_text="Podstawy, z których pozycję można dziś zwrócić",
    )
    claim_requests = serializers.ListField(
        child=serializers.ChoiceField(choices=ClaimRequest.choices),
        read_only=True,
        help_text="Żądania dostępne przy reklamacji tej pozycji",
    )
    exchange_available = serializers.BooleanField(
        read_only=True,
        help_text=(
            "Czy wymiana na ten sam wariant jest dziś możliwa (#198) — "
            "ostateczną dostępność sprawdza przyjęcie zgłoszenia"
        ),
    )


class ReturnRequestItemSerializer(serializers.ModelSerializer):
    """Pozycja zgłoszenia z decyzją sklepu."""

    product_name = serializers.CharField(
        source="order_item.product_name", read_only=True
    )
    sku = serializers.CharField(source="order_item.sku", read_only=True)
    agreed_amount = MoneySerializer(
        source="agreed_money", read_only=True, allow_null=True
    )

    class Meta:
        model = ReturnRequestItem
        fields = [
            "id",
            "order_item",
            "product_name",
            "sku",
            "quantity",
            "claim_request",
            "status",
            "decision_note",
            "agreed_resolution",
            "agreed_amount",
            "decided_at",
        ]
        read_only_fields = fields


class ReturnRequestSerializer(serializers.ModelSerializer):
    """Zgłoszenie zwrotu w postaci dla klienta."""

    items = ReturnRequestItemSerializer(many=True, read_only=True)
    compensation_amount = MoneySerializer(
        source="compensation_money",
        read_only=True,
        allow_null=True,
        help_text="Zwracana kwota; pusta, dopóki zgłoszenia nie rozliczono",
    )
    coupon_code = serializers.CharField(
        source="coupon.code",
        read_only=True,
        allow_null=True,
        default=None,
        help_text="Kod kuponu wydanego z kuponowej części zwrotu",
    )
    coupon_amount = MoneySerializer(
        source="coupon.nominal_money",
        read_only=True,
        allow_null=True,
        default=None,
        help_text="Nominał kuponu ze zwrotu",
    )
    refund_amount = MoneySerializer(
        source="refund_money",
        read_only=True,
        allow_null=True,
        help_text="Pieniężna część zwrotu; pusta, dopóki nie rozliczono",
    )

    class Meta:
        model = ReturnRequest
        fields = [
            "id",
            "reason",
            "status",
            "items",
            "compensation_amount",
            "coupon_code",
            "coupon_amount",
            "refund_amount",
            "refund_status",
            "created_at",
        ]
        read_only_fields = fields


class ReturnLineWriteSerializer(serializers.Serializer):
    order_item = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    claim_request = serializers.ChoiceField(
        choices=ClaimRequest.choices,
        required=False,
        default="",
        allow_blank=True,
        help_text="Wymagane przy reklamacji, niedozwolone przy innej podstawie",
    )


class ReturnRequestCreateSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(choices=ReturnReason.choices)
    items = ReturnLineWriteSerializer(many=True, allow_empty=False)
