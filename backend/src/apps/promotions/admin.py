from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

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
    readonly_fields = ("announced_at",)
    actions = ["announce", "reset_announcement"]

    @admin.action(description="Ogłoś promocję klientom")
    def announce(self, request: HttpRequest, queryset: QuerySet[Promotion]) -> None:
        """E-mail do zgód i subskrypcji, push do zgód push — w tle, raz na promocję."""
        from apps.notifications.newsletter import queue_promotion_announcement

        queued = [p for p in queryset if queue_promotion_announcement(p)]
        skipped = queryset.count() - len(queued)
        self.message_user(
            request,
            f"Zakolejkowano ogłoszeń: {len(queued)}; pominięto już ogłoszonych: {skipped}.",
        )

    @admin.action(description="Zresetuj ogłoszenie (pozwól ogłosić ponownie)")
    def reset_announcement(
        self, request: HttpRequest, queryset: QuerySet[Promotion]
    ) -> None:
        """Po nieudanej wysyłce — ponowne ogłoszenie może zdublować część maili."""
        from apps.notifications.newsletter import reset_promotion_announcement

        reset = reset_promotion_announcement(queryset)
        self.message_user(request, f"Zresetowano ogłoszeń: {reset}.")


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

    def get_readonly_fields(self, request, obj=None) -> tuple[str, ...]:
        """Wydany kupon to zobowiązanie sklepu — kodu, nominału ani statusu się nie przepisuje."""
        if obj is not None and obj.pk:
            return ("code", "nominal", "currency", "status")
        return ()
