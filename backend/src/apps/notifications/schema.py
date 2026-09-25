from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.notifications.serializers import (
    NotificationPreferenceSerializer,
    NotificationSerializer,
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
