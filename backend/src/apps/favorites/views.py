from __future__ import annotations

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.favorites.schema import favorite_schema
from apps.favorites.serializers import (
    FavoriteMergeSerializer,
    FavoriteSerializer,
    FavoriteWriteSerializer,
)
from apps.favorites.services import (
    add_favorite,
    favorites_for,
    merge_favorites,
    remove_favorite,
)


@favorite_schema
class FavoriteViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Ulubione produkty klienta (`CONTEXT.md`, Favorite).

    Actions:
    - list:    GET    /favorites/          — ulubione, produkty opublikowane
    - create:  POST   /favorites/          — dodanie (idempotentne)
    - destroy: DELETE /favorites/{slug}/   — usunięcie (idempotentne)
    - merge:   POST   /favorites/merge/    — scalenie listy gościa po logowaniu

    Tylko dla zalogowanego — gość trzyma listę wyłącznie u siebie w aplikacji.
    Adres detalu wskazuje produkt (`slug`), nie wpis ulubionych — klient zna
    slug produktu z karty, nie identyfikator wpisu. Nazwa parametru zostaje
    jednoczłonowa: `djangorestframework_camel_case` camelizuje nazwy
    parametrów w schemacie, nie sam adres URL — `product_slug` rozjeżdżałby
    się z wygenerowanym `productSlug` i wywracał walidację klienta Orval.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = FavoriteSerializer
    lookup_field = "product__slug"
    lookup_url_kwarg = "slug"

    def get_queryset(self):
        return favorites_for(self.request.user)  # type: ignore[bad-argument-type]

    def create(self, request: Request, *args, **kwargs) -> Response:
        payload = FavoriteWriteSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        favorite = add_favorite(
            user=request.user, product=payload.validated_data["product"]
        )
        return Response(
            FavoriteSerializer(favorite).data, status=status.HTTP_201_CREATED
        )

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Usunięcie po slugu produktu — brak dopasowania to też 204 (idempotentne)."""
        remove_favorite(user=request.user, product_slug=kwargs["slug"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"])
    def merge(self, request: Request, *args, **kwargs) -> Response:
        """Lista identyfikatorów (slugów) produktów od gościa → suma z listą konta."""
        payload = FavoriteMergeSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        merged = merge_favorites(
            user=request.user, product_slugs=payload.validated_data["products"]
        )
        return Response(FavoriteSerializer(merged, many=True).data)
