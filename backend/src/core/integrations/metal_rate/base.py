from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from common.money import DEFAULT_CURRENCY


@dataclass(frozen=True, slots=True)
class MetalQuote:
    """Notowanie kruszcu przyniesione z zewnątrz.

    Nie jest modelem: dopóki właściciel go nie zatwierdzi, notowanie nie ma
    prawa niczego zmienić w katalogu (ADR 0022).
    """

    metal: str
    fineness: str
    price_per_gram: int
    quoted_on: date
    source: str
    currency: str = DEFAULT_CURRENCY


class MetalRateProvider(Protocol):
    """Źródło notowań kruszców.

    Dostawca nie jest jeszcze wybrany (ADR 0027), więc interfejs jest wąski
    celowo: zwraca notowania i nic poza tym. Zamiana dostawcy to nowa klasa
    i zmiana konfiguracji, nie migracja danych.
    """

    def quotes(self) -> list[MetalQuote]: ...
