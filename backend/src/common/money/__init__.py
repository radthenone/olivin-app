"""Warstwa pieniędzy: kwoty jako liczby całkowite w najmniejszej jednostce waluty.

Konwencja z ADR 0009 — żadna kwota nie jest liczbą zmiennoprzecinkową, a
zaokrąglenie następuje raz, na poziomie pozycji, nigdy w trakcie sumowania.
"""

from common.money.allocation import allocate, split_evenly
from common.money.fields import CurrencyField, MoneyAmountField
from common.money.money import DEFAULT_CURRENCY, CurrencyMismatchError, Money
from common.money.vat import VatBreakdown, split_gross

__all__ = [
    "DEFAULT_CURRENCY",
    "CurrencyField",
    "CurrencyMismatchError",
    "Money",
    "MoneyAmountField",
    "VatBreakdown",
    "allocate",
    "split_evenly",
    "split_gross",
]
