from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view

from apps.products.models import EURO
from apps.products.serializers import ProductDetailSerializer, ProductListSerializer
from apps.translations.schema import LANGUAGE_PARAMETER
from common.money import DEFAULT_CURRENCY

CURRENCY_PARAMETER = OpenApiParameter(
    name="currency",
    type=str,
    location=OpenApiParameter.QUERY,
    enum=[DEFAULT_CURRENCY, EURO],
    description=(
        "Waluta cen. EUR przelicza ceny złotowe po bieżącym kursie NBP "
        "i zaokrągla w górę do ,00/,50 (ADR 0019); brak kursu daje 400. "
        "Filtry i progi (cena, darmowa dostawa) zawsze działają w złotych."
    ),
)

product_schema = extend_schema_view(
    list=extend_schema(
        parameters=[LANGUAGE_PARAMETER, CURRENCY_PARAMETER],
        tags=["Products"],
        summary="Lista opublikowanych produktów",
        description=(
            "Zwraca wyłącznie produkty opublikowane. Każdy z nich reprezentuje "
            "jego najtańszy wariant; produkt bez wariantów ma tu wartość pustą."
        ),
        responses={200: ProductListSerializer(many=True)},
    ),
    retrieve=extend_schema(
        parameters=[LANGUAGE_PARAMETER, CURRENCY_PARAMETER],
        tags=["Products"],
        summary="Produkt wraz z pełną listą wariantów",
        description=(
            "Adresem jest slug. Szkic nie jest dostępny pod żadnym adresem — "
            "odpowiedzią jest 404, tak samo jak dla produktu nieistniejącego."
        ),
        responses={200: ProductDetailSerializer},
    ),
)
