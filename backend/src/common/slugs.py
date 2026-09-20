"""Slugi katalogu — angielskie, unikalne, niezmienne po opublikowaniu.

Zasada jest wspólna dla kategorii, produktów i kolekcji, więc mieszka tutaj,
a nie w którejkolwiek z aplikacji: inaczej `products` musiałoby importować
`categories` po to jedno pole.

Angielska forma bierze się z **tłumaczenia nazwy**, nie z nazwy polskiej
pozbawionej ogonków. „Pierścionki zaręczynowe" mają dać `engagement-rings`,
a nie `pierscionki-zareczynowe` — a ponieważ slug jest niezmienny, pomyłka tu
zostaje w adresie na stałe.
"""

from __future__ import annotations

from typing import Any

from django.db import models
from django.utils.text import slugify

SLUG_MAX_LENGTH = 140

# `slugify` rozkłada znaki diakrytyczne przez NFKD i odrzuca to, co zostanie
# poza ASCII. Polskie „ł" nie jest literą z ogonkiem, tylko osobnym znakiem bez
# rozkładu — bez tej podmiany „Łańcuszki" dają slug `ancuszki`. Podmiana jest
# nadal potrzebna, bo tłumaczenie bywa nazwą własną, która zostaje po polsku.
_POLISH_ASCII = str.maketrans({"ł": "l", "Ł": "L"})


class SlugSourceUnavailable(RuntimeError):
    """Nie ma z czego zbudować angielskiego sluga.

    Osobny wyjątek, bo jedyną alternatywą byłby cichy odwrót do nazwy
    polskiej — czyli dokładnie ten błąd, który ta warstwa ma usuwać.
    """


def polish_to_ascii(value: str) -> str:
    return value.translate(_POLISH_ASCII)


def slugify_name(name: str, fallback: str) -> str:
    """Zamienia gotowy tekst na slug. Nie tłumaczy niczego."""
    return slugify(polish_to_ascii(name))[:SLUG_MAX_LENGTH] or fallback


def english_slug(obj, field: str, fallback: str) -> str:
    """Slug z angielskiego brzmienia pola `field`.

    Kolejność jest celowa: najpierw gotowe tłumaczenie, dopiero potem
    wywołanie silnika. Publikacja zwykle następuje po tym, jak tłumaczenie
    już powstało, więc typowy zapis nie rusza sieci.

    Rzuca `SlugSourceUnavailable`, gdy angielskiej nazwy nie da się zdobyć —
    wywołujący ma wtedy odrzucić zapis i poprosić o slug wpisany ręcznie,
    a nie podstawić nazwę polską.
    """
    from apps.translations.models import Language
    from apps.translations.service import english_name

    name = english_name(obj, field, Language.EN)
    if not name:
        raise SlugSourceUnavailable(
            f"Brak angielskiego brzmienia pola „{field}” — nie ma z czego "
            "zbudować adresu."
        )
    return slugify_name(name, fallback)


def unique_slug(
    model: type[models.Model],
    base: str,
    exclude_pk: Any = None,
) -> str:
    """Dokłada przyrostek, dopóki slug jest zajęty.

    Kolizja jest realna: „Gold rings" i „Gold, rings" dają ten sam slug,
    a kolumna jest unikalna.
    """
    taken = model._default_manager.exclude(pk=exclude_pk)
    candidate = base
    suffix = 2
    while taken.filter(slug=candidate).exists():
        tail = f"-{suffix}"
        candidate = f"{base[: SLUG_MAX_LENGTH - len(tail)]}{tail}"
        suffix += 1
    return candidate
