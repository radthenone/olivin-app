from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.reviews.serializers import (
    MyReviewSerializer,
    ProductToReviewSerializer,
    ReviewCreateSerializer,
    ReviewUpdateSerializer,
)

review_schema = extend_schema_view(
    list=extend_schema(
        tags=["Reviews"],
        summary="Własne opinie klienta",
        description="Wszystkie opinie zalogowanego klienta, niezależnie od statusu moderacji.",
        responses={200: MyReviewSerializer(many=True)},
    ),
    create=extend_schema(
        tags=["Reviews"],
        summary="Nowa opinia",
        description=(
            "Wymaga dostarczonego zamówienia z tym produktem i jednej opinii "
            "na klienta na produkt. Opinia trafia do moderacji."
        ),
        request=ReviewCreateSerializer,
        responses={201: MyReviewSerializer},
    ),
    partial_update=extend_schema(
        tags=["Reviews"],
        summary="Edycja opinii",
        description="Edycja treści i oceny — opinia wraca do moderacji.",
        request=ReviewUpdateSerializer,
        responses={200: MyReviewSerializer},
    ),
    to_review=extend_schema(
        tags=["Reviews"],
        summary="Produkty do oceny",
        description="Produkty z dostarczonych zamówień, których klient jeszcze nie ocenił.",
        responses={200: ProductToReviewSerializer(many=True)},
    ),
)
