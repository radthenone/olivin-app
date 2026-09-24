from __future__ import annotations

from django.db.models import QuerySet
from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny

from apps.promotions.models import Promotion
from apps.promotions.schema import promotion_schema
from apps.promotions.serializers import PromotionSerializer


@promotion_schema
class PromotionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Promocje sklepu.

    Actions:
    - list: GET /promotions/ — aktywne promocje bez kodu

    Tylko odczyt: promocje zakłada właściciel w panelu (ADR 0021).
    """

    permission_classes = [AllowAny]
    serializer_class = PromotionSerializer

    def get_queryset(self) -> QuerySet[Promotion]:
        return (
            Promotion.objects.active()
            .filter(code="")
            .prefetch_related("products", "collections", "categories")
            .order_by("-starts_at", "-id")
        )
