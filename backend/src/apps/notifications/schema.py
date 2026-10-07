from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.notifications.serializers import (
    NewsletterDetailSerializer,
    NewsletterSubscribeSerializer,
    NewsletterTokenSerializer,
    NotificationPreferenceSerializer,
    NotificationSerializer,
    PushDeviceSerializer,
    PushDeviceWriteSerializer,
)

notification_schema = extend_schema_view(
    list=extend_schema(
        tags=["Notifications"],
        summary="Lista powiadomień klienta",
        responses={200: NotificationSerializer(many=True)},
    ),
    read=extend_schema(
        tags=["Notifications"],
        summary="Oznaczenie powiadomienia jako odczytane",
        request=None,
        responses={200: NotificationSerializer},
    ),
)

notification_preference_schema = extend_schema_view(
    get=extend_schema(
        tags=["Notifications"],
        summary="Preferencje powiadomień klienta",
        responses={200: NotificationPreferenceSerializer},
    ),
    put=extend_schema(
        tags=["Notifications"],
        summary="Zmiana preferencji powiadomień",
        request=NotificationPreferenceSerializer,
        responses={200: NotificationPreferenceSerializer},
    ),
)

push_device_schema = extend_schema_view(
    list=extend_schema(
        tags=["Notifications"],
        summary="Lista urządzeń push klienta",
        responses={200: PushDeviceSerializer(many=True)},
    ),
    create=extend_schema(
        tags=["Notifications"],
        summary="Rejestracja urządzenia push",
        request=PushDeviceWriteSerializer,
        responses={201: PushDeviceSerializer},
    ),
    destroy=extend_schema(
        tags=["Notifications"],
        summary="Wyrejestrowanie urządzenia push",
        request=None,
        responses={204: None},
    ),
)

newsletter_subscribe_schema = extend_schema(
    tags=["Notifications"],
    summary="Zapis na newsletter",
    description=(
        "Bez logowania. Zawsze 202 z tą samą treścią — odpowiedź nie zdradza, "
        "czy adres był już zapisany. Na adres trafia link potwierdzenia; "
        "400, gdy brak bieżącej wersji zgody marketingowej."
    ),
    request=NewsletterSubscribeSerializer,
    responses={202: NewsletterDetailSerializer},
)

newsletter_confirm_schema = extend_schema(
    tags=["Notifications"],
    summary="Potwierdzenie zapisu na newsletter",
    description="Token z linku w mailu potwierdzenia. 404 dla nieznanego tokenu.",
    request=NewsletterTokenSerializer,
    responses={200: NewsletterDetailSerializer},
)

newsletter_unsubscribe_schema = extend_schema(
    tags=["Notifications"],
    summary="Wypis z newslettera",
    description=(
        "Bez logowania, token z linku w stopce maila — subskrypcji albo konta "
        "(wyłącza wtedy zgodę marketingową e-mail konta). 404 dla nieznanego tokenu."
    ),
    request=NewsletterTokenSerializer,
    responses={200: NewsletterDetailSerializer},
)
