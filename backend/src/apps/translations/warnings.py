"""Ostrzeżenie o rozjeździe tekstu źródłowego z poprawką ręczną."""

from __future__ import annotations

from collections.abc import Iterable

from apps.translations.models import Translation, TranslationSource
from apps.translations.registry import fields_for


def stale_manual_fields(obj, changed_fields: Iterable[str]) -> list[str]:
    """Pola zmienione w tym zapisie, które mają poprawione ręcznie tłumaczenie.

    Automat takiego wpisu nie ruszy, więc bez ostrzeżenia poprawiony po polsku
    opis zostałby po angielsku w poprzednim brzmieniu i nikt by się nie
    dowiedział.

    Bierzemy pola faktycznie zmienione w formularzu, a nie znacznik
    `updated_at`: ten przesuwa się przy każdym zapisie, więc ostrzeżenie
    wyskakiwałoby też po poprawieniu ceny albo kategorii. Ostrzeżenie, które
    pojawia się zawsze, przestaje cokolwiek znaczyć.
    """
    if obj.pk is None:
        return []

    watched = set(fields_for(obj)) & set(changed_fields)
    if not watched:
        return []

    manual = Translation.objects.for_object(obj).filter(
        source=TranslationSource.MANUAL, field__in=watched
    )
    return sorted(translation.field for translation in manual)
