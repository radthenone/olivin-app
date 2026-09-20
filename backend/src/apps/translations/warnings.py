"""Ostrzeżenie o rozjeździe tekstu źródłowego z poprawką ręczną."""

from __future__ import annotations

from apps.translations.models import Translation, TranslationSource
from apps.translations.registry import fields_for


def stale_manual_fields(obj) -> list[str]:
    """Pola, które mają poprawione ręcznie tłumaczenie starsze od zmiany tekstu.

    Automat takiego wpisu nie ruszy, więc bez ostrzeżenia poprawiony po polsku
    opis zostałby po angielsku w poprzednim brzmieniu i nikt by się nie
    dowiedział.
    """
    if obj.pk is None or obj.updated_at is None:
        return []

    manual = Translation.objects.for_object(obj).filter(
        source=TranslationSource.MANUAL, field__in=fields_for(obj)
    )
    return [
        translation.field
        for translation in manual
        if translation.translated_at < obj.updated_at
    ]
