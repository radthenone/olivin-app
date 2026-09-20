"""Parametr języka w opisie API katalogu."""

from drf_spectacular.utils import OpenApiParameter

from apps.translations.language import QUERY_PARAM
from apps.translations.models import SOURCE_LANGUAGE, Language

LANGUAGE_PARAMETER = OpenApiParameter(
    name=QUERY_PARAM,
    type=str,
    location=OpenApiParameter.QUERY,
    enum=[SOURCE_LANGUAGE, *(choice.value for choice in Language)],
    description=(
        "Język pól tekstowych. Bez tego parametru brany jest nagłówek "
        "`Accept-Language`, a w jego braku polski. Brakujące tłumaczenie "
        "schodzi do tekstu polskiego; slug nie jest tłumaczony."
    ),
)
