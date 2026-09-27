from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.inventory.models import (
    AVAILABLE,
    ON_HAND,
    RESERVED,
    InventoryItem,
    InventoryItemQuerySet,
    Reservation,
    StockMovement,
)


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
    list_display = (
        "variant",
        "on_hand_display",
        "reserved_display",
        "available_display",
    )
    search_fields = ("variant__sku", "variant__product__name")
    ordering = ("variant__sku",)
    autocomplete_fields = ("variant",)

    def get_queryset(self, request: HttpRequest) -> QuerySet[InventoryItem]:
        # `with_stock()`, a nie właściwości modelu: te liczą po dwa agregaty
        # na wiersz, więc lista stanów robiłaby zapytanie na każdą pozycję.
        # Stub `ModelAdmin.get_queryset` zwraca goły `QuerySet`, więc gubi
        # metody własnego queryu — patrz komentarz przy `Product.objects`.
        base: InventoryItemQuerySet = super().get_queryset(request)  # type: ignore[bad-assignment]
        return base.with_stock().select_related("variant", "variant__product")

    @admin.display(description="Stan z ruchów", ordering=ON_HAND)
    def on_hand_display(self, obj: InventoryItem) -> int:
        return getattr(obj, ON_HAND)

    @admin.display(description="Zarezerwowane", ordering=RESERVED)
    def reserved_display(self, obj: InventoryItem) -> int:
        return getattr(obj, RESERVED)

    @admin.display(description="Dostępne", ordering=AVAILABLE)
    def available_display(self, obj: InventoryItem) -> int:
        return getattr(obj, AVAILABLE)


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


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """Rezerwacje do wglądu — zakłada je kasa, zwalnia zadanie okresowe.

    Panel ich nie zakłada i nie edytuje: rezerwacja bez zamówienia, które ją
    uzasadnia, trzymałaby stan bez powodu i nikt by jej nie zwolnił.
    """

    list_display = ("variant", "quantity", "status", "expires_at", "created_at")
    list_filter = ("status",)
    search_fields = ("variant__sku",)
    ordering = ("-created_at",)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Reservation]:
        return super().get_queryset(request).select_related("variant")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False
