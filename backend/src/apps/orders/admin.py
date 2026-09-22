from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.orders.models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    """Pozycje przy koszyku — do wglądu, nie do poprawiania.

    Koszyk prowadzi klient. Panel ma go pokazać przy rozmowie z obsługą
    („co pani ma w koszyku"), a nie zmieniać za plecami klienta.
    """

    model = CartItem
    extra = 0
    fields = ("variant", "quantity", "engraving_text", "second_size")
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Koszyki do wglądu — także po to, żeby zobaczyć, co czeka na sprzątanie."""

    inlines = [CartItemInline]
    list_display = ("__str__", "item_count_display", "last_activity_at")
    list_filter = ("last_activity_at",)
    search_fields = ("user__email", "session_key")
    ordering = ("-last_activity_at",)
    readonly_fields = ("user", "session_key", "last_activity_at")

    def get_queryset(self, request: HttpRequest) -> QuerySet[Cart]:
        return super().get_queryset(request).select_related("user")

    @admin.display(description="Pozycji")
    def item_count_display(self, obj: Cart) -> int:
        return obj.item_count

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False
