from __future__ import annotations

from rest_framework import serializers

from apps.notifications.models import Notification, NotificationPreference


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
