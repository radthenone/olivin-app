from __future__ import annotations

from datetime import date
from decimal import Decimal

import requests

from core.integrations.exchange_rate.base import RateQuote

# Tabela A: średnie kursy walut obcych, publikowane w dni robocze.
API_URL = "https://api.nbp.pl/api/exchangerates/rates/A/{currency}/?format=json"
TIMEOUT_SECONDS = 20
SOURCE = "nbp"


class NbpProvider:
    """Kurs średni Narodowego Banku Polskiego (ADR 0019, ADR 0027).

    API publiczne i bez klucza, więc adapter nie potrzebuje konfiguracji.
    """

    def quote(self, currency: str) -> RateQuote:
        response = requests.get(
            API_URL.format(currency=currency.upper()), timeout=TIMEOUT_SECONDS
        )
        response.raise_for_status()
        latest = response.json()["rates"][-1]
        return RateQuote(
            currency=currency.upper(),
            # Przez str: `mid` przychodzi jako float z JSON-a.
            rate=Decimal(str(latest["mid"])),
            quoted_on=date.fromisoformat(latest["effectiveDate"]),
            source=SOURCE,
        )
