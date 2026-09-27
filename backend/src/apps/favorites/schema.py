from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.favorites.serializers import (
    FavoriteMergeSerializer,
    FavoriteSerializer,
    FavoriteWriteSerializer,
)

favorite_schema = extend_schema_view(
    list=extend_schema(
        tags=["Favorites"],
        summary="Ulubione produkty",
        description="Ulubione klienta; produkt cofnięty do szkicu znika z listy.",
        responses={200: FavoriteSerializer(many=True)},
    ),
    create=extend_schema(
        tags=["Favorites"],
        summary="Dodanie do ulubionych",
        description="Idempotentne — dodanie już ulubionego produktu nie jest błędem.",
        request=FavoriteWriteSerializer,
        responses={201: FavoriteSerializer},
    ),
    destroy=extend_schema(
        tags=["Favorites"],
        summary="Usunięcie z ulubionych",
        description="Idempotentne — brak dopasowania też kończy się 204.",
        responses={204: None},
    ),
    merge=extend_schema(
        tags=["Favorites"],
        summary="Scalenie listy gościa",
        description=(
            "Identyfikatory (slugi) produktów z listy gościa trafiają do listy "
            "konta; nieistniejące i nieopublikowane są pomijane."
        ),
        request=FavoriteMergeSerializer,
        responses={200: FavoriteSerializer(many=True)},
    ),
)
