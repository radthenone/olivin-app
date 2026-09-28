from django.contrib import admin
from django.http import HttpRequest

from apps.watches.models import Watch


@admin.register(Watch)
class WatchAdmin(admin.ModelAdmin):
    """Podgląd obserwowanych — bez edycji, klient zarządza listą sam przez API."""

    list_display = ("user", "variant", "kind", "status", "created_at")
    list_filter = ("kind", "status")
    search_fields = ("user__email", "variant__sku")
    ordering = ("-created_at",)
    readonly_fields = ("user", "variant", "kind", "price_at_watch", "status")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False
