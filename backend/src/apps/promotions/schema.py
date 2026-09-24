from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.promotions.serializers import PromotionSerializer

promotion_schema = extend_schema_view(
    list=extend_schema(
        tags=["Promotions"],
        summary="Aktywne promocje bez kodu",
        description=(
            "Promocje w okresie obowiązywania, które działają bez kodu. "
            "Zakres to identyfikatory produktów, kolekcji i kategorii "
            "(kategoria obejmuje podkategorie) albo `wholeCatalog`. Promocje "
            "kodowe nie są tu wymieniane — kod zna ten, komu sklep go dał."
        ),
        responses={200: PromotionSerializer(many=True)},
    ),
)
