from django.contrib import admin

from apps.consents.models import Consent, ConsentDocument


@admin.register(ConsentDocument)
class ConsentDocumentAdmin(admin.ModelAdmin):
    """Nowa wersja dokumentu to nowy wpis, nie edycja starego (`CONTEXT.md`, Consent)."""

    list_display = ("kind", "version", "effective_from")
    list_filter = ("kind",)
    ordering = ("kind", "-effective_from")


@admin.register(Consent)
class ConsentAdmin(admin.ModelAdmin):
    """Rejestr zgód — do wglądu, nie do edycji: zgodę daje klient, nie panel."""

    list_display = ("subject", "document", "version", "granted_at")
    list_filter = ("document__kind",)
    search_fields = ("email", "user__email")
    readonly_fields = ("user", "email", "document", "version", "granted_at")
    ordering = ("-granted_at",)

    @admin.display(description="Podmiot")
    def subject(self, obj: Consent) -> str:
        return obj.email if obj.user_id is None else obj.user.email  # type: ignore[missing-attribute]

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False
