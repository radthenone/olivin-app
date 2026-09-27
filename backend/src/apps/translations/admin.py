from django.contrib import admin, messages
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.contenttypes.forms import BaseGenericInlineFormSet
from django.utils import timezone
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.translations.models import Translation, TranslationSource


class TranslationInlineFormSet(BaseGenericInlineFormSet):
    """Zapis tłumaczenia z panelu to zawsze poprawka człowieka.

    Znakowanie siedzi w zbiorze formularzy, a nie w `save_model` inline'u:
    `InlineModelAdmin` nie ma takiej metody, więc ustawianie tam źródła było
    kodem, którego nic nie woła.
    """

    def _mark_manual(self, obj: Translation, commit: bool) -> Translation:
        obj.source = TranslationSource.MANUAL
        obj.translated_at = timezone.now()
        if commit:
            obj.save()
        return obj

    def save_new(self, form, commit: bool = True) -> Translation:
        return self._mark_manual(super().save_new(form, commit=False), commit)

    def save_existing(self, form, obj, commit: bool = True) -> Translation:
        return self._mark_manual(super().save_existing(form, obj, commit=False), commit)


class TranslationInline(GenericTabularInline):
    """Tłumaczenia przy obiekcie katalogu.

    Zapis z panelu oznacza wpis jako poprawiony ręcznie — automat nigdy go
    już nie nadpisze. To jedyny sposób, w jaki `manual` powstaje: właściciel
    poprawia tekst, bo silnik się pomylił.
    """

    model = Translation
    formset = TranslationInlineFormSet
    ct_field = "content_type"
    ct_fk_field = "object_id"
    extra = 0
    fields = ("field", "language", "text", "source", "translated_at")
    readonly_fields = ("source", "translated_at")


@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    """Przegląd tłumaczeń katalogu."""

    list_display = ("field", "language", "source", "translated_at", "target")
    list_filter = ("language", "source", "field")
    search_fields = ("text",)
    ordering = ("-translated_at",)
    readonly_fields = ("content_type", "object_id", "translated_at")
    actions = ("mark_manual",)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Translation]:
        return super().get_queryset(request).select_related("content_type")

    def save_model(self, request, obj, form, change) -> None:
        # Każda edycja z panelu to poprawka człowieka.
        obj.source = TranslationSource.MANUAL
        obj.translated_at = timezone.now()
        super().save_model(request, obj, form, change)

    @admin.action(description="Oznacz jako poprawione ręcznie")
    def mark_manual(
        self, request: HttpRequest, queryset: QuerySet[Translation]
    ) -> None:
        updated = queryset.update(source=TranslationSource.MANUAL)
        self.message_user(
            request,
            f"Oznaczono {updated} tłumaczeń jako poprawione ręcznie.",
            messages.SUCCESS,
        )
