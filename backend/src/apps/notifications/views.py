from __future__ import annotations

from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.notifications.models import Notification, NotificationPreference
from apps.notifications.schema import (
    notification_preference_schema,
    notification_schema,
)
from apps.notifications.serializers import (
    NotificationPreferenceSerializer,
    NotificationSerializer,
)


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
