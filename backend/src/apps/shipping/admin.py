from django.contrib import admin

from apps.shipping.models import Shipment, ShippingMethod


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    """Cennik dostawy prowadzi właściciel w panelu — API go tylko czyta (ADR 0021)."""

    list_display = ("name", "kind", "zone", "rate", "max_order_value", "is_active")
    list_filter = ("zone", "kind", "is_active")
    search_fields = ("name",)
    ordering = ("zone", "rate", "name")
    # Waluty nie ma w formularzu: ceny źródłowe są złotowe (ADR 0019), a metoda
    # wyceniona w euro dziś nie wyszłaby do żadnego klienta — przeliczenie
    # stawek przyjdzie razem ze sprzedażą do Unii.
    fields = ("name", "kind", "zone", "rate", "max_order_value", "is_active")


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    """Przesyłki wpisywane ręcznie (ADR 0027).

    Numer śledzenia i wartość zadeklarowana biorą się z serwisu przewoźnika,
    bo adaptera przewoźnika jeszcze nie ma. Klient tej wartości nie widzi —
    ubezpieczenie jest wliczone w stawkę (ADR 0028).
    """

    list_display = ("order", "tracking_number", "declared_value", "pickup_point_code")
    list_filter = ("order__status",)
    search_fields = ("tracking_number", "order__number")
    ordering = ("-created_at",)
    autocomplete_fields = ("order",)
