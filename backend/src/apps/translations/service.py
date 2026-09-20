"""Odczyt i zapis tłumaczeń katalogu."""

from __future__ import annotations

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from apps.translations.models import (
    SOURCE_LANGUAGE,
    Language,
    Translation,
    TranslationSource,
)
from apps.translations.registry import fields_for
from core.integrations.translation import get_provider


def translated_value(obj, field: str, language: str | None) -> str:
    """Tekst w wybranym języku z odwrotem na polski.

    Fallback jest po to, żeby świeżo opublikowany produkt był czytelny
    zanim zadanie w tle skończy pracę — pusty tytuł byłby gorszy niż tytuł
    po polsku.

    Czyta z `obj.translations.all()`, więc przy `prefetch_related` nie dobija
    bazy na każde pole.
    """
    source = getattr(obj, field, "") or ""
    if not language or language == SOURCE_LANGUAGE:
        return source
    for translation in obj.translations.all():
        if translation.field == field and translation.language == language:
            return translation.text or source
    return source


def missing_fields(obj, language: str = Language.EN) -> list[str]:
    """Pola, które nie mają jeszcze tłumaczenia i mają co tłumaczyć."""
    existing = {
        translation.field
        for translation in obj.translations.all()
        if translation.language == language
    }
    return [
        field
        for field in fields_for(obj)
        if field not in existing and (getattr(obj, field, "") or "").strip()
    ]


def translate_object(obj, language: str = Language.EN) -> int:
    """Uzupełnia brakujące tłumaczenia obiektu.

    Nie rusza wpisów poprawionych ręcznie i nie nadpisuje tych, które już są:
    zadanie okresowe chodzi po katalogu wielokrotnie i za każdym razem ma
    dokładać, a nie przepisywać od nowa.
    """
    fields = missing_fields(obj, language)
    if not fields:
        return 0

    texts = get_provider().translate(
        [getattr(obj, field) for field in fields],
        target_language=language,
        source_language=SOURCE_LANGUAGE,
    )
    content_type = ContentType.objects.get_for_model(obj)
    now = timezone.now()

    created = 0
    for field, text in zip(fields, texts, strict=True):
        _, is_new = Translation.objects.get_or_create(
            content_type=content_type,
            object_id=obj.pk,
            field=field,
            language=language,
            defaults={
                "text": text,
                "source": TranslationSource.AUTO,
                "translated_at": now,
            },
        )
        created += int(is_new)
    return created
