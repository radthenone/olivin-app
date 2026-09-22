from django.contrib import admin
from django.db.models import Count, QuerySet
from django.http import HttpRequest

from apps.orders.models import Cart, CartItem, Order, OrderItem


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
        return (
            super()
            .get_queryset(request)
            .select_related("user")
            # Adnotacja, nie `Cart.item_count`: to drugie robi zapytanie na
            # każdy wiersz listy.
            .annotate(items_total=Count("items"))
        )

    @admin.display(description="Pozycji", ordering="items_total")
    def item_count_display(self, obj: Cart) -> int:
        return obj.items_total  # type: ignore[missing-attribute]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


class OrderItemInline(admin.TabularInline):
    """Pozycje zamówienia — do wglądu, nigdy do edycji.

    Pozycja jest kopią z chwili złożenia (ADR 0010). Poprawienie jej
    w panelu oznaczałoby, że faktura i historia zaczynają kłamać; korektę
    robi się zwrotem, nie edycją.
    """

    model = OrderItem
    extra = 0
    fields = (
        "sku",
        "product_name",
        "quantity",
        "unit_price",
        "engraving_text",
        "second_size",
    )
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Obsługa zamówień w panelu (ADR 0021).

    Edytowalny jest wyłącznie status, i to przez akcje odpowiadające
    dozwolonym przejściom — pole wyboru pozwalałoby cofnąć wysłane
    zamówienie do `pending`, czego cykl życia nie przewiduje.
    """

    inlines = [OrderItemInline]
    list_display = ("number", "status", "email", "total_display", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("number", "email", "user__email")
    ordering = ("-created_at",)
    readonly_fields = tuple(
        field.name for field in Order._meta.fields if field.name != "status"
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Order]:
        return (
            super()
            .get_queryset(request)
            .select_related("user", "shipping_method")
            .prefetch_related("items")
        )

    @admin.display(description="Do zapłaty")
    def total_display(self, obj: Order) -> str:
        return str(obj.total)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def save_model(self, request: HttpRequest, obj: Order, form, change) -> None:
        """Zmiana statusu idzie przez `transition_to`, nie przez zapis pola.

        Dzięki temu ograniczenia cyklu życia obowiązują tak samo z panelu,
        jak z API — nakładka panelu nie przejmuje logiki domenowej (ADR 0021).
        """
        if not change:
            super().save_model(request, obj, form, change)
            return
        previous = Order.objects.get(pk=obj.pk)
        if previous.status != obj.status:
            obj.status = previous.status
            obj.transition_to(form.cleaned_data["status"])
            return
        super().save_model(request, obj, form, change)
