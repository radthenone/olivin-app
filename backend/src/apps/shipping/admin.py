from django.contrib import admin

from apps.shipping.models import ShippingMethod


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
