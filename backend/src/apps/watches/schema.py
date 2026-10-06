from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.watches.serializers import WatchSerializer, WatchWriteSerializer

watch_schema = extend_schema_view(
    list=extend_schema(
        tags=["Watches"],
        summary="Obserwowane warianty",
        description="Aktywne prośby klienta o powiadomienie (restock / price_drop).",
        responses={200: WatchSerializer(many=True)},
    ),
    create=extend_schema(
        tags=["Watches"],
        summary="Dodanie obserwowania",
        description=(
            "Przycisk „powiadom mnie” przy niedostępnym wariancie (restock) "
            "i przy cenie (price_drop). Idempotentne dla aktywnej prośby."
        ),
        request=WatchWriteSerializer,
        responses={201: WatchSerializer},
    ),
    destroy=extend_schema(
        tags=["Watches"],
        summary="Usunięcie obserwowania",
        description="Idempotentne — brak dopasowania też kończy się 204.",
        responses={204: None},
    ),
)
