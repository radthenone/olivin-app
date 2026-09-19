from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.categories.serializers import CategorySerializer

category_schema = extend_schema_view(
    list=extend_schema(
        tags=["Categories"],
        summary="Drzewo kategorii",
        description=(
            "Zwraca korzenie taksonomii wraz z całym zagnieżdżeniem. "
            "Odpowiedź nie jest stronicowana — gałąź bez korzenia nie jest "
            "drzewem."
        ),
        responses={200: CategorySerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=["Categories"],
        summary="Gałąź drzewa od wskazanej kategorii",
        description=(
            "Zwraca wskazaną kategorię wraz z jej zagnieżdżonymi potomkami. "
            "Adresem jest slug, nie identyfikator."
        ),
        responses={200: CategorySerializer},
    ),
)
