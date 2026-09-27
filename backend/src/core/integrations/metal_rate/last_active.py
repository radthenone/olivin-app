from __future__ import annotations

from datetime import date

from core.integrations.metal_rate.base import MetalQuote

SOURCE = "last-active"


class LastActiveRateProvider:
    """Dostawca zastępczy: powtarza ostatni zatwierdzony kurs.

    Dostawca notowań nie jest wybrany (ADR 0027), a do czasu wyboru kurs
    wpisuje się ręcznie. Ten adapter istnieje po to, żeby zadanie okresowe
    miało co wołać i żeby jego wynik — propozycja identyczna z tym, co już
    obowiązuje — był jawnie bezczynny, zamiast zgadywać cenę kruszcu.
    """

    def quotes(self) -> list[MetalQuote]:
        from apps.products.models.metal_rate import MetalRate

        today = date.today()
        return [
            MetalQuote(
                metal=rate.metal,
                fineness=rate.fineness,
                price_per_gram=rate.price_per_gram,
                currency=rate.currency,
                quoted_on=today,
                source=SOURCE,
            )
            for rate in MetalRate.objects.active()
        ]
