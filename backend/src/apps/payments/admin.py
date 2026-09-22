from django.contrib import admin
from django.http import HttpRequest

from apps.payments.models import Payment, WebhookEvent


class _ReadOnlyAdmin(admin.ModelAdmin):
    """Zapis wyłącznie przez zdarzenia operatora — panel tylko pokazuje.

    Ręczna zmiana statusu płatności rozjechałaby się z tym, co operator
    faktycznie obciążył; zwrot robi się anulowaniem albo w panelu operatora.
    """

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


@admin.register(Payment)
class PaymentAdmin(_ReadOnlyAdmin):
    list_display = (
        "intent_id",
        "order",
        "amount",
        "currency",
        "status",
        "refund_reason",
        "created_at",
    )
    list_filter = ("status", "refund_reason")
    search_fields = ("intent_id", "order__number", "order__email")
    list_select_related = ("order",)


@admin.register(WebhookEvent)
class WebhookEventAdmin(_ReadOnlyAdmin):
    list_display = ("event_id", "kind", "processed_at", "created_at")
    list_filter = ("kind",)
    search_fields = ("event_id",)
