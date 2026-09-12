from __future__ import annotations

from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.money.money import DEFAULT_CURRENCY


class MoneyAmountField(models.BigIntegerField):
    """Kolumna na kwotę w najmniejszej jednostce waluty (ADR 0009).

    Osobna klasa zamiast gołego BigIntegerField, żeby w schemacie i w migracjach
    było widać, że kolumna trzyma grosze — i żeby nikt nie dopisał DecimalField
    "bo tak jest wygodniej". Znak jest dozwolony: korekty i zwroty są ujemne.
    """

    description = _("Kwota w najmniejszej jednostce waluty")

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("help_text", "Kwota w najmniejszej jednostce waluty (grosze)")
        super().__init__(*args, **kwargs)


class CurrencyField(models.CharField):
    """Kod waluty ISO 4217 towarzyszący każdej kolumnie MoneyAmountField."""

    description = _("Kod waluty ISO 4217")

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("max_length", 3)
        kwargs.setdefault("default", DEFAULT_CURRENCY)
        kwargs.setdefault("help_text", "Kod waluty ISO 4217")
        kwargs.setdefault(
            "validators",
            [
                RegexValidator(
                    r"^[A-Z]{3}$", "Kod waluty to trzy wielkie litery ISO 4217"
                )
            ],
        )
        super().__init__(*args, **kwargs)
