from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.inventory.models import InventoryItem, StockMovement


class StockMovementInline(admin.TabularInline):
    """Ruchy przy stanie — jedyne miejsce, w którym stan się zmienia.

    Ruch zapisany nie da się już poprawić: stan jest sumą wierszy, więc
    korektę robi się kolejnym ruchem, a nie edycją poprzedniego. Inaczej
    historia przestałaby tłumaczyć, skąd wziął się dzisiejszy stan.
    """

    model = StockMovement
    extra = 1
    fields = ("quantity", "reason", "note", "created_at")
    readonly_fields = ("created_at",)

    def get_readonly_fields(
        self, request: HttpRequest, obj: InventoryItem | None = None
    ) -> tuple[str, ...]:
        return ("created_at",)

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    """Magazyn prowadzony w panelu; API tylko pokazuje wynik (ADR 0021)."""

    inlines = [StockMovementInline]
    list_display = ("variant", "on_hand_display", "reserved", "available_display")
    search_fields = ("variant__sku", "variant__product__name")
    ordering = ("variant__sku",)
    autocomplete_fields = ("variant",)

    def get_queryset(self, request: HttpRequest) -> QuerySet[InventoryItem]:
        return (
            super()
            .get_queryset(request)
            .select_related("variant", "variant__product")
            .prefetch_related("movements")
        )

    @admin.display(description="Stan z ruchów")
    def on_hand_display(self, obj: InventoryItem) -> int:
        return obj.on_hand

    @admin.display(description="Dostępne")
    def available_display(self, obj: InventoryItem) -> int:
        return obj.available


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    """Dziennik ruchów — do przeglądania, nie do poprawiania."""

    list_display = ("item", "quantity", "reason", "note", "created_at")
    list_filter = ("reason",)
    search_fields = ("item__variant__sku", "note")
    ordering = ("-created_at",)

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False
