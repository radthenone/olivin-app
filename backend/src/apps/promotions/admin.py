from django.contrib import admin

from apps.promotions.models import Promotion, PromotionRedemption


class PromotionRedemptionInline(admin.TabularInline):
    """Zastosowania promocji — do wglądu; powstają przy składaniu zamówienia."""

    model = PromotionRedemption
    extra = 0
    fields = ("order", "amount", "created_at")
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None) -> bool:
        return False


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    """Panel promocji — jedyne miejsce, w którym powstają i się zmieniają."""

    inlines = [PromotionRedemptionInline]
    list_display = ("name", "kind", "value", "code", "starts_at", "ends_at")
    list_filter = ("kind", "whole_catalog", "requires_premium")
    search_fields = ("name", "code")
    filter_horizontal = ("products", "collections", "categories")
