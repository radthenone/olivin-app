from __future__ import annotations

from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.notifications.models import Notification, NotificationPreference
from apps.notifications.schema import (
    notification_preference_schema,
    notification_schema,
    push_device_schema,
)
from apps.notifications.serializers import (
    NotificationPreferenceSerializer,
    NotificationSerializer,
    PushDeviceSerializer,
    PushDeviceWriteSerializer,
)
from apps.notifications.services import register_push_device, unregister_push_device


@notification_schema
class NotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Powiadomienia klienta.

    Actions:
    - list: GET /notifications/ — powiadomienia zalogowanego klienta
    - read: POST /notifications/{id}/read/ — oznaczenie jako odczytane
    """

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        notification = self.get_object()
        notification.mark_read()
        return Response(
            self.get_serializer(notification).data, status=status.HTTP_200_OK
        )


@notification_preference_schema
class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    """Preferencje powiadomień marketingowych klienta (`GET`/`PUT`).

    Bez `PATCH`: dwa pola, oba zawsze przekazywane razem — jak przy edycji
    profilu w jednym formularzu.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationPreferenceSerializer
    http_method_names = ["get", "put", "options"]

    def get_object(self) -> NotificationPreference:
        return NotificationPreference.for_user(self.request.user)  # type: ignore[bad-argument-type]


@push_device_schema
class PushDeviceViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Urządzenia push klienta (`CONTEXT.md`, PushDevice).

    Actions:
    - list: GET /notifications/devices/ — urządzenia zalogowanego klienta
    - create: POST /notifications/devices/ — rejestracja (idempotentna)
    - destroy: DELETE /notifications/devices/{token}/ — wyrejestrowanie

    Rejestracja po zalogowaniu w aplikacji mobilnej, wyrejestrowanie przy
    wylogowaniu. Token w adresie jest URL-kodowany przez klienta.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = PushDeviceSerializer
    lookup_field = "token"
    lookup_url_kwarg = "token"

    def get_queryset(self):
        from apps.notifications.models import PushDevice

        return PushDevice.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs) -> Response:
        payload = PushDeviceWriteSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        device = register_push_device(
            user=request.user,
            token=payload.validated_data["token"],
            platform=payload.validated_data["platform"],
        )
        return Response(
            PushDeviceSerializer(device).data, status=status.HTTP_201_CREATED
        )

    def destroy(self, request, *args, **kwargs) -> Response:
        """Wyrejestrowanie po tokenie — brak dopasowania to też 204."""
        unregister_push_device(user=request.user, token=kwargs["token"])
        return Response(status=status.HTTP_204_NO_CONTENT)
