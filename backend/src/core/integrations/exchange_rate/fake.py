from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import ClassVar

from core.integrations.exchange_rate.base import RateQuote

SOURCE = "fake"


class FakeExchangeRateProvider:
    """Atrapa kursu do testów i pracy bez sieci — stały kurs z dzisiejszą datą."""

    rate: ClassVar[Decimal] = Decimal("4.250000")

    def quote(self, currency: str) -> RateQuote:
        return RateQuote(
            currency=currency.upper(),
            rate=self.rate,
            quoted_on=date.today(),
            source=SOURCE,
        )
