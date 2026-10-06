from __future__ import annotations

from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications import newsletter

from apps.notifications.models import Notification, NotificationPreference
from apps.notifications.schema import (
    newsletter_confirm_schema,
    newsletter_subscribe_schema,
    newsletter_unsubscribe_schema,
    notification_preference_schema,
    notification_schema,
    push_device_schema,
)
from apps.notifications.serializers import (
    NewsletterSubscribeSerializer,
    NewsletterTokenSerializer,
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


class _PublicNewsletterView(APIView):
    """Wspólne dla endpointów newslettera: dla każdego, bez sesji.

    Bez uwierzytelnienia, więc bez wymogu CSRF z sesji — linki z maila
    otwiera się bez logowania. Zakres `auth`: zapis wysyła maile na
    dowolny adres, a tokeny nie mają być zgadywane seriami.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "auth"


class NewsletterSubscribeView(_PublicNewsletterView):
    """`POST /notifications/newsletter/subscribe/` — zapis (double opt-in)."""

    @newsletter_subscribe_schema
    def post(self, request: Request) -> Response:
        payload = NewsletterSubscribeSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            newsletter.subscribe(payload.validated_data["email"])
        except newsletter.NoMarketingDocumentError as exc:
            raise ValidationError(
                {"email": "Zapis chwilowo niedostępny — brak zgody marketingowej."}
            ) from exc
        return Response(
            {"detail": "Sprawdź skrzynkę — wysłaliśmy link potwierdzenia."},
            status=status.HTTP_202_ACCEPTED,
        )


class NewsletterConfirmView(_PublicNewsletterView):
    """`POST /notifications/newsletter/confirm/` — potwierdzenie linkiem."""

    @newsletter_confirm_schema
    def post(self, request: Request) -> Response:
        payload = NewsletterTokenSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        if not newsletter.confirm(payload.validated_data["token"]):
            raise NotFound("Link potwierdzenia jest nieważny albo już użyty.")
        return Response({"detail": "Zapis na newsletter potwierdzony."})


class NewsletterUnsubscribeView(_PublicNewsletterView):
    """`POST /notifications/newsletter/unsubscribe/` — wypis bez logowania."""

    @newsletter_unsubscribe_schema
    def post(self, request: Request) -> Response:
        payload = NewsletterTokenSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        if not newsletter.unsubscribe(payload.validated_data["token"]):
            raise NotFound("Link wypisu jest nieważny.")
        return Response({"detail": "Wypisano z newslettera."})
