from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import Count, QuerySet
from django.http import HttpRequest

from apps.orders.models import (
    Cart,
    CartItem,
    Order,
    OrderItem,
    OrderStatus,
    ReturnItemStatus,
    ReturnRefundStatus,
    ReturnRequest,
    ReturnRequestItem,
)
from apps.orders.services.returns import decide_return_item, validate_decision


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


class ReturnRequestItemForm(forms.ModelForm):
    """Decyzja o pozycji zgłoszenia — reguły z `validate_decision`, nie z panelu.

    Sprawdzenie w `clean()`, żeby obsługa zobaczyła komunikat przy pozycji,
    a nie błąd serwera przy zapisie (jak w `OrderAdminForm`).
    """

    decision = forms.ChoiceField(
        label="Decyzja",
        required=False,
        choices=[
            ("", "—"),
            (ReturnItemStatus.ACCEPTED, ReturnItemStatus.ACCEPTED.label),
            (ReturnItemStatus.REJECTED, ReturnItemStatus.REJECTED.label),
        ],
    )

    class Meta:
        model = ReturnRequestItem
        fields = ("restocked", "decision_note", "agreed_resolution", "agreed_amount")
        labels = {"restocked": "Wraca na stan"}

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # Inline nie ma `get_readonly_fields` per wiersz (dostaje zgłoszenie,
        # nie pozycję), więc rozstrzygnięty wiersz blokuje się w formularzu:
        # pole `disabled` pokazuje wartość i ignoruje to, co przyszło w POST.
        if self.instance.pk is not None and not self.instance.is_open:
            for field in self.fields.values():
                field.disabled = True

    def clean(self) -> dict:
        cleaned = super().clean() or {}
        if cleaned.get("decision"):
            try:
                validate_decision(self.instance, **self.decision_kwargs(cleaned))
            except ValidationError as error:
                raise forms.ValidationError(error.messages) from error
        return cleaned

    @staticmethod
    def decision_kwargs(cleaned: dict) -> dict:
        return {
            "status": cleaned["decision"],
            "restock": bool(cleaned.get("restocked")),
            "note": cleaned.get("decision_note") or "",
            "agreed_resolution": cleaned.get("agreed_resolution") or "",
            "agreed_amount": cleaned.get("agreed_amount"),
        }


class ReturnRequestItemInline(admin.TabularInline):
    model = ReturnRequestItem
    form = ReturnRequestItemForm
    extra = 0
    can_delete = False
    fields = (
        "order_item",
        "quantity",
        "claim_request",
        "status",
        "decision",
        "restocked",
        "decision_note",
        "agreed_resolution",
        "agreed_amount",
        "decided_at",
        "exchange_order",
    )
    readonly_fields = (
        "order_item",
        "quantity",
        "claim_request",
        "status",
        "decided_at",
        "exchange_order",
    )

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    """Rozpatrywanie zgłoszeń zwrotu — decyzja osobno dla każdej pozycji.

    Zapis pozycji idzie wyłącznie przez `decide_return_item()` (ADR 0021):
    tam powstaje ruch magazynowy, stan zgłoszenia i powiadomienie. Wiersz
    bez wybranej decyzji nie zmienia się wcale.
    """

    inlines = [ReturnRequestItemInline]
    list_display = ("__str__", "reason", "status", "refund_status", "created_at")
    list_filter = ("status", "refund_status", "reason", "created_at")
    search_fields = ("order__number", "order__email")
    ordering = ("-created_at",)
    readonly_fields = (
        "order",
        "reason",
        "status",
        "compensation_amount",
        "coupon",
        "refund_amount",
        "refund_status",
        "refund_id",
        "settled_at",
    )
    actions = ["mark_manual_refund_done"]

    @admin.action(description="Oznacz przelew zwrotu jako wykonany")
    def mark_manual_refund_done(
        self, request: HttpRequest, queryset: QuerySet[ReturnRequest]
    ) -> None:
        """Pieniądze oddane przelewem po odmowie operatora (ADR 0031)."""
        manual = list(queryset.filter(refund_status=ReturnRefundStatus.MANUAL))
        for return_request in manual:
            return_request.refund_status = ReturnRefundStatus.MANUAL_DONE
            return_request.save(update_fields=["refund_status", "updated_at"])
            self.log_change(request, return_request, "Przelew zwrotu wykonany ręcznie")
        self.message_user(request, f"Oznaczono przelewy: {len(manual)}.")

    def get_queryset(self, request: HttpRequest) -> QuerySet[ReturnRequest]:
        return super().get_queryset(request).select_related("order")

    def save_formset(self, request, form, formset, change) -> None:
        if formset.model is not ReturnRequestItem:
            super().save_formset(request, form, formset, change)
            return
        # Historia zmian w panelu czyta te listy, które normalnie wypełnia
        # `formset.save()` — tu zapis idzie obok niego.
        formset.new_objects, formset.deleted_objects = [], []
        formset.changed_objects = []
        for item_form in formset.forms:
            if not item_form.cleaned_data.get("decision"):
                continue
            try:
                decide_return_item(
                    item_form.instance,
                    **ReturnRequestItemForm.decision_kwargs(item_form.cleaned_data),
                )
            except ValidationError as error:
                # Reguła złamana między walidacją formularza a zapisem, np.
                # równoległa decyzja o tej samej pozycji — komunikat, nie 500.
                messages.error(
                    request, f"{item_form.instance}: {' '.join(error.messages)}"
                )
                continue
            formset.changed_objects.append((item_form.instance, ["status"]))

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False
