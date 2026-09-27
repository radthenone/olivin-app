"""Wyszukiwanie po nazwie i opisie produktu.

Docelowym silnikiem jest pełnotekstowe wyszukiwanie PostgreSQL — bez
Elasticsearcha. Testy jednostkowe chodzą jednak na SQLite w pamięci
(`core/settings/testing.py`), a `SearchVector` jest wyrażeniem, którego
SQLite nie zna: zapytanie kończy się błędem, nie gorszym wynikiem.

Stąd jeden szew z dwiema realizacjami wybieranymi po silniku połączenia.
Na produkcji i w testach integracyjnych działa `SearchVector`; poza nimi
dopasowanie po fragmencie tekstu, które daje wynik zbliżony na tyle, żeby
test filtru miał sens. Gałąź postgresową pokrywa test z markerem
`integration`.
"""

from __future__ import annotations

from django.db import connection
from django.db.models import Q, QuerySet

SEARCHED_FIELDS = ("name", "description")


def supports_full_text() -> bool:
    return connection.vendor == "postgresql"


def search(queryset: QuerySet, phrase: str) -> QuerySet:
    """Zawęża listę do produktów pasujących nazwą albo opisem."""
    phrase = phrase.strip()
    if not phrase:
        return queryset
    if supports_full_text():
        return _search_full_text(queryset, phrase)
    return _search_substring(queryset, phrase)


def _search_full_text(queryset: QuerySet, phrase: str) -> QuerySet:
    from django.contrib.postgres.search import SearchQuery, SearchVector

    vector = SearchVector(*SEARCHED_FIELDS, config="simple")
    query = SearchQuery(phrase, config="simple", search_type="websearch")
    return queryset.annotate(search_vector=vector).filter(search_vector=query)


def _search_substring(queryset: QuerySet, phrase: str) -> QuerySet:
    condition = Q()
    for field in SEARCHED_FIELDS:
        condition |= Q(**{f"{field}__icontains": phrase})
    return queryset.filter(condition)
