"""Język treści wybrany przez klienta."""

from __future__ import annotations

from apps.translations.models import SOURCE_LANGUAGE, Language

SUPPORTED = {choice.value for choice in Language} | {SOURCE_LANGUAGE}
QUERY_PARAM = "lang"


def language_from(request) -> str:
    """`?lang=` ma pierwszeństwo przed `Accept-Language`.

    Parametr w adresie jest jawnym wyborem klienta — nagłówek tylko
    ustawieniem przeglądarki albo telefonu. Język spoza listy schodzi do
    polskiego, bo tekst źródłowy jest zawsze dostępny.
    """
    if request is None:
        return SOURCE_LANGUAGE

    requested = (request.query_params.get(QUERY_PARAM) or "").strip().lower()
    if requested:
        return requested if requested in SUPPORTED else SOURCE_LANGUAGE

    header = request.headers.get("Accept-Language", "")
    for part in header.split(","):
        tag = part.split(";")[0].strip().lower().split("-")[0]
        if tag in SUPPORTED:
            return tag
    return SOURCE_LANGUAGE
