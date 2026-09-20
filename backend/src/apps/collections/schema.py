from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.collections.serializers import CollectionSerializer
from apps.translations.schema import LANGUAGE_PARAMETER

collection_schema = extend_schema_view(
    list=extend_schema(
        parameters=[LANGUAGE_PARAMETER],
        tags=["Collections"],
        summary="Lista kolekcji",
        description=(
            "Zwraca kolekcje, w których jest co najmniej jeden opublikowany "
            "produkt. Produkty kolekcji pobiera się przez "
            "`GET /products/?collection=<slug>`."
        ),
        responses={200: CollectionSerializer(many=True)},
    ),
    retrieve=extend_schema(
        parameters=[LANGUAGE_PARAMETER],
        tags=["Collections"],
        summary="Pojedyncza kolekcja",
        description="Adresem jest slug. Pusta kolekcja to 404.",
        responses={200: CollectionSerializer},
    ),
)
