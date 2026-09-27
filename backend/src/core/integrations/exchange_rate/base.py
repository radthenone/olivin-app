from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol

from common.money import DEFAULT_CURRENCY


@dataclass(frozen=True, slots=True)
class RateQuote:
    """Notowanie kursu waluty: ile złotych kosztuje jedna jednostka `currency`."""

    currency: str
    rate: Decimal
    quoted_on: date
    source: str
    base_currency: str = DEFAULT_CURRENCY


class ExchangeRateProvider(Protocol):
    """Źródło kursu walut (ADR 0027) — zwraca notowanie i nic poza tym."""

    def quote(self, currency: str) -> RateQuote: ...
