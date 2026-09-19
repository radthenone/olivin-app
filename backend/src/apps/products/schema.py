from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.products.serializers import ProductDetailSerializer, ProductListSerializer

product_schema = extend_schema_view(
    list=extend_schema(
        tags=["Products"],
        summary="Lista opublikowanych produktów",
        description=(
            "Zwraca wyłącznie produkty opublikowane. Każdy z nich reprezentuje "
            "jego najtańszy wariant; produkt bez wariantów ma tu wartość pustą."
        ),
        responses={200: ProductListSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=["Products"],
        summary="Produkt wraz z pełną listą wariantów",
        description=(
            "Adresem jest slug. Szkic nie jest dostępny pod żadnym adresem — "
            "odpowiedzią jest 404, tak samo jak dla produktu nieistniejącego."
        ),
        responses={200: ProductDetailSerializer},
    ),
)
