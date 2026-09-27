from __future__ import annotations

from celery import shared_task

from apps.translations.models import Language
from apps.translations.registry import translatable_models
from apps.translations.service import missing_fields, translate_object


def _published_only(model, queryset):
    """Szkice są pomijane — tłumaczy się to, co klient może zobaczyć."""
    from apps.products.models import ProductStatus

    if hasattr(model, "status"):
        return queryset.filter(status=ProductStatus.PUBLISHED)
    if model._meta.label == "products.ProductImage":
        return queryset.filter(product__status=ProductStatus.PUBLISHED)
    return queryset


@shared_task
def translate_catalog_object(
    label: str, object_id: str, language: str = Language.EN
) -> int:
    """Uzupełnia tłumaczenia jednego obiektu katalogu."""
    from django.apps import apps as django_apps

    model = django_apps.get_model(label)
    obj = model.objects.filter(pk=object_id).prefetch_related("translations").first()
    if obj is None:
        return 0
    return translate_object(obj, language)


@shared_task
def translate_published_catalog(language: str = Language.EN) -> int:
    """Obchodzi opublikowany katalog i dokłada brakujące tłumaczenia.

    Zadanie okresowe jest drugim wyzwalaczem obok publikacji: pierwszy
    obsługuje nowe produkty, to wyłapuje wszystko, czego tamten nie dowiózł —
    padnięte zadanie, tekst dopisany po publikacji, nowy język.
    """
    translated = 0
    for model in translatable_models():
        queryset = _published_only(model, model.objects.all()).prefetch_related(
            "translations"
        )
        # `chunk_size` jest wymagany przy `iterator()` po `prefetch_related` —
        # bez niego Django nie wie, na ile obiektów naraz dociągnąć relację.
        # Katalog obchodzimy partiami, żeby nie wczytywać go w całości.
        for obj in queryset.iterator(chunk_size=200):
            if missing_fields(obj, language):
                translated += translate_object(obj, language)
    return translated
