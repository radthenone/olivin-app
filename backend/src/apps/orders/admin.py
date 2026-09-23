from django import forms
from django.contrib import admin
from django.db.models import Count, QuerySet
from django.http import HttpRequest

from apps.orders.models import Cart, CartItem, Order, OrderItem, OrderStatus


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


class OrderAdminForm(forms.ModelForm):
    """Formularz zamówienia, który odrzuca niedozwolone przejście statusu.

    Sprawdzenie jest w `clean_status`, a nie dopiero w `save_model`: wyjątek
    rzucony przy zapisie wychodzi w panelu jako błąd serwera, a obsługa ma
    zobaczyć komunikat przy polu, tak jak przy każdej innej pomyłce.
    """

    class Meta:
        model = Order
        fields = "__all__"

    def clean_status(self) -> str:
        status = self.cleaned_data["status"]
        if self.instance.pk is None or status == self.instance.status:
            return status
        previous = Order.objects.get(pk=self.instance.pk)
        if not previous.can_transition_to(status):
            raise forms.ValidationError(
                f"Ze statusu „{previous.get_status_display()}” nie da się "
                f"przejść do „{OrderStatus(status).label}”."
            )
        return status


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Obsługa zamówień w panelu (ADR 0021).

    Edytowalny jest wyłącznie status, i to w granicach cyklu życia: formularz
    odrzuca przejście, którego `ALLOWED_TRANSITIONS` nie przewiduje, więc nie
    da się cofnąć wysłanego zamówienia do `pending`. Te same reguły obowiązują
    z panelu i z API — nakładka nie przejmuje logiki domenowej (ADR 0021).
    """

    form = OrderAdminForm
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
