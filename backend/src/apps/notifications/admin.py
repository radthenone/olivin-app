from django.contrib import admin

from apps.notifications.models import Notification, NotificationPreference, PushDevice


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Powiadomienia — do wglądu, zapisuje je wyłącznie `notify()`."""

    list_display = ("user", "kind", "is_read", "created_at")
    list_filter = ("kind", "is_read")
    search_fields = ("user__email",)
    readonly_fields = ("user", "kind", "message", "data", "read_at")
    ordering = ("-created_at",)

    def has_add_permission(self, request) -> bool:
        return False


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "marketing_email", "marketing_push")
    search_fields = ("user__email",)


@admin.register(PushDevice)
class PushDeviceAdmin(admin.ModelAdmin):
    """Urządzenia push — do wglądu; zapisują je rejestracje z aplikacji."""

    list_display = ("user", "platform", "last_used_at", "created_at")
    list_filter = ("platform",)
    search_fields = ("user__email", "token")
    readonly_fields = ("user", "token", "platform", "last_used_at")
