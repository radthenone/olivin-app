from __future__ import annotations

from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.shipping.models import ShippingMethod
from apps.shipping.schema import shipping_method_schema
from apps.shipping.serializers import (
    ShippingMethodQuerySerializer,
    ShippingOfferSerializer,
)
from apps.shipping.services import available_methods
from common.money import Money


@shipping_method_schema
class ShippingMethodViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Metody dostawy dostępne dla koszyka o podanej wartości.

    Actions:
    - list: GET /shipping-methods/?order_value=&zone= — metody wraz z kosztem

    Dla każdego, bo gość wybiera dostawę przed założeniem konta. Tylko
    odczyt: cennik prowadzi panel (ADR 0021). Bez stronicowania — metod jest
    kilka, a krok trzeci kasy potrzebuje ich wszystkich naraz.
    """

    permission_classes = [AllowAny]
    serializer_class = ShippingOfferSerializer
    pagination_class = None
    filter_backends: list = []
    queryset = ShippingMethod.objects.none()

    def list(self, request: Request, *args, **kwargs) -> Response:
        query = ShippingMethodQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)

        # Bez pośredniej metody z adnotacją `list[ShippingOffer]`: w ciele
        # klasy `list` to zdefiniowana wyżej akcja widoku, nie typ wbudowany.
        offers = available_methods(
            order_value=Money(query.validated_data["order_value"]),
            zone=query.validated_data["zone"],
        )
        return Response(self.get_serializer(offers, many=True).data)
