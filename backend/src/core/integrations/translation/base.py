from __future__ import annotations

from typing import Protocol


class TranslationProvider(Protocol):
    """Silnik tłumaczenia treści katalogu (ADR 0027).

    Interfejs przyjmuje listę tekstów, a nie pojedynczy: obaj dostawcy liczą
    zapytania, a produkt ma nazwę i opis — wysłanie ich razem to jedno wywołanie
    zamiast dwóch.
    """

    def translate(
        self,
        texts: list[str],
        *,
        target_language: str,
        source_language: str,
    ) -> list[str]: ...
