"""Waluta z `?currency=` — wspólna dla katalogu, koszyka i dostawy (ADR 0019)."""

from __future__ import annotations

from rest_framework import serializers

from apps.products.models import EURO, ExchangeRate
from common.money import DEFAULT_CURRENCY

QUERY_PARAM = "currency"


def requested_rate(currency: str | None) -> ExchangeRate | None:
    """Kurs dla żądanej waluty; `None` dla cen w złotych.

    Brak kursu euro to 400, a nie cicha zamiana na złote: klient z Unii
    zobaczyłby kwotę w innej walucie, niż prosił.
    """
    currency = (currency or DEFAULT_CURRENCY).upper()
    if currency == DEFAULT_CURRENCY:
        return None
    if currency != EURO:
        raise serializers.ValidationError(
            {QUERY_PARAM: f"Obsługiwane waluty: {DEFAULT_CURRENCY}, {EURO}."}
        )
    rate = ExchangeRate.objects.current(EURO)
    if rate is None:
        raise serializers.ValidationError(
            {QUERY_PARAM: "Kurs euro nie jest jeszcze dostępny."}
        )
    return rate
