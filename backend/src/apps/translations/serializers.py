"""Pola tekstowe podawane w języku wybranym przez klienta."""

from __future__ import annotations

from rest_framework import serializers

from apps.translations.language import language_from
from apps.translations.service import translated_value


class TranslatedCharField(serializers.CharField):
    """Pole tekstowe, które sięga po tłumaczenie z odwrotem na polski.

    Tłumaczenia są odczytywane z `obj.translations.all()`, więc widok, który
    je prefetchuje, nie dobija bazy — a widok, który zapomni, i tak zwróci
    poprawną treść, tylko drożej.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("read_only", True)
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        return instance

    def to_representation(self, value) -> str:
        language = language_from(self.context.get("request"))
        return translated_value(value, self.field_name or "", language)
