from django.contrib import admin

from apps.promotions.models import (
    Coupon,
    CouponRedemption,
    Promotion,
    PromotionRedemption,
)


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


class CouponRedemptionInline(admin.TabularInline):
    """Użycia kuponu — do wglądu; powstają przy składaniu zamówienia."""

    model = CouponRedemption
    extra = 0
    fields = ("order", "amount", "created_at")
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None) -> bool:
        return False


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """Panel kuponów — sklep wydaje kupon z kodem, nominałem z listy i terminem."""

    inlines = [CouponRedemptionInline]
    list_display = ("code", "nominal", "status", "source", "expires_at")
    list_filter = ("status", "source")
    search_fields = ("code",)
