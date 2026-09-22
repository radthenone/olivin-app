from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.shipping.serializers import (
    ShippingMethodQuerySerializer,
    ShippingOfferSerializer,
)

shipping_method_schema = extend_schema_view(
    list=extend_schema(
        tags=["Shipping"],
        summary="Metody dostawy dostępne dla koszyka",
        description=(
            "Zwraca metody właściwe dla strefy, których górna wartość "
            "zamówienia nie została przekroczona, wraz z kosztem policzonym "
            "dla podanej wartości koszyka. Powyżej progu darmowej dostawy "
            "koszt wynosi zero. Odbiór osobisty nie ma górnej wartości "
            "zamówienia, więc jest na liście zawsze."
        ),
        parameters=[ShippingMethodQuerySerializer],
        responses={200: ShippingOfferSerializer(many=True)},
    ),
)
