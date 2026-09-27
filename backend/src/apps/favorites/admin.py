from django.contrib import admin
from django.http import HttpRequest

from apps.favorites.models import Favorite


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Podgląd ulubionych — bez edycji, klient zarządza listą sam przez API."""

    list_display = ("user", "product", "created_at")
    search_fields = ("user__username", "user__email", "product__name")
    ordering = ("-created_at",)
    readonly_fields = ("user", "product", "created_at", "updated_at")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False
