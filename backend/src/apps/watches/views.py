from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.watches.models import Watch
from apps.watches.schema import watch_schema
from apps.watches.serializers import (
    WatchSerializer,
    WatchWriteSerializer,
)
from apps.watches.services import add_watch, remove_watch, watches_for


@watch_schema
class WatchViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Obserwowane warianty klienta (`CONTEXT.md`, Watch).

    Actions:
    - list:    GET    /watches/       — aktywne prośby klienta
    - create:  POST   /watches/       — dodanie (idempotentne)
    - destroy: DELETE /watches/{id}/  — usunięcie (idempotentne)

    Tylko dla zalogowanego. Produkt na zamówienie: tylko `price_drop`.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = WatchSerializer
    queryset = Watch.objects.none()

    def get_queryset(self):
        return watches_for(self.request.user)  # type: ignore[bad-argument-type]

    def create(self, request: Request, *args, **kwargs) -> Response:
        payload = WatchWriteSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            watch = add_watch(
                user=request.user,
                variant=payload.validated_data["variant"],
                kind=payload.validated_data["kind"],
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.message_dict)
        return Response(WatchSerializer(watch).data, status=status.HTTP_201_CREATED)

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Usunięcie po id wpisu — cudzy wpis nie znika (idempotentne 204).

        Usunięcie jest idempotentne także dla identyfikatora, który nie jest
        UUID: filtr z taką wartością rzuciłby `ValidationError` z warstwy
        modelu, a klient wołający „przestań obserwować” ma dostać 204.
        """
        try:
            remove_watch(user=request.user, watch_id=kwargs["pk"])  # type: ignore[bad-argument-type]
        except DjangoValidationError:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)
