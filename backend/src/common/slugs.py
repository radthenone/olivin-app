"""Slugi katalogu — angielskie, unikalne, niezmienne po opublikowaniu.

Zasada jest wspólna dla kategorii, produktów i kolekcji, więc mieszka tutaj,
a nie w którejkolwiek z aplikacji: inaczej `products` musiałoby importować
`categories` po to jedno pole.
"""

from __future__ import annotations

from typing import Any

from django.db import models
from django.utils.text import slugify

SLUG_MAX_LENGTH = 140

# `slugify` rozkłada znaki diakrytyczne przez NFKD i odrzuca to, co zostanie
# poza ASCII. Polskie „ł" nie jest literą z ogonkiem, tylko osobnym znakiem bez
# rozkładu — bez tej podmiany „Łańcuszki" dają slug `ancuszki`, a ponieważ slug
# jest niezmienny, literówka w adresie zostaje na stałe.
_POLISH_ASCII = str.maketrans({"ł": "l", "Ł": "L"})


def polish_to_ascii(value: str) -> str:
    return value.translate(_POLISH_ASCII)


def slug_base(name: str, fallback: str) -> str:
    """Punkt wyjścia sluga: nazwa bez polskich znaków, przycięta do kolumny."""
    return slugify(polish_to_ascii(name))[:SLUG_MAX_LENGTH] or fallback


def unique_slug(
    model: type[models.Model],
    base: str,
    exclude_pk: Any = None,
) -> str:
    """Dokłada przyrostek, dopóki slug jest zajęty.

    Kolizja jest realna: „Pierścionki złote" i „Pierścionki, złote" dają ten
    sam slug, a kolumna jest unikalna.
    """
    taken = model._default_manager.exclude(pk=exclude_pk)
    candidate = base
    suffix = 2
    while taken.filter(slug=candidate).exists():
        tail = f"-{suffix}"
        candidate = f"{base[: SLUG_MAX_LENGTH - len(tail)]}{tail}"
        suffix += 1
    return candidate
