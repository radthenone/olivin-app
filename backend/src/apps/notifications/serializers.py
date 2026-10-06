from __future__ import annotations

from rest_framework import serializers

from apps.notifications.models import Notification, NotificationPreference, PushDevice


class NotificationSerializer(serializers.ModelSerializer):
    """Powiadomienie klienta — tylko do odczytu; oznaczenie odczytania ma osobny endpoint."""

    class Meta:
        model = Notification
        fields = ["id", "kind", "message", "data", "is_read", "read_at", "created_at"]
        read_only_fields = fields


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Zgoda marketingowa klienta, osobno per kanał."""

    class Meta:
        model = NotificationPreference
        fields = ["marketing_email", "marketing_push"]


class PushDeviceSerializer(serializers.ModelSerializer):
    """Urządzenie push — zapis po tokenie; odczyt bez wrażliwych pól."""

    class Meta:
        model = PushDevice
        fields = ["token", "platform", "last_used_at"]
        read_only_fields = ["last_used_at"]


class PushDeviceWriteSerializer(serializers.Serializer):
    """Rejestracja urządzenia: token Expo i platforma."""

    token = serializers.CharField(max_length=255)
    platform = serializers.ChoiceField(choices=["ios", "android"])

    def validate_token(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Token nie może być pusty.")
        return value


class NewsletterSubscribeSerializer(serializers.Serializer):
    """Zapis na newsletter — sam adres; zgodę marketingową dobiera backend."""

    email = serializers.EmailField(help_text="Adres do zapisu")


class NewsletterTokenSerializer(serializers.Serializer):
    """Token z linku w mailu — potwierdzenia albo wypisu."""

    token = serializers.CharField(max_length=512, help_text="Token z linku w mailu")


class NewsletterDetailSerializer(serializers.Serializer):
    """Komunikat do wyświetlenia po zapisie, potwierdzeniu albo wypisie."""

    detail = serializers.CharField(read_only=True)
