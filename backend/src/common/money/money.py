from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Final

DEFAULT_CURRENCY: Final = "PLN"

# Liczba cyfr po przecinku w jednostce głównej. Brak wpisu oznacza 2 (ISO 4217
# dla zdecydowanej większości walut); wyjątki dopisujemy, gdy pojawi się waluta.
_MINOR_DIGITS: Final[dict[str, int]] = {"JPY": 0, "KRW": 0, "ISK": 0}

_CURRENCY_RE: Final = re.compile(r"^[A-Z]{3}$")


class CurrencyMismatchError(ValueError):
    """Operacja na dwóch kwotach w różnych walutach."""


def minor_digits(currency: str) -> int:
    return _MINOR_DIGITS.get(currency, 2)


@dataclass(frozen=True, slots=True)
class Money:
    """Kwota jako liczba całkowita groszy plus kod waluty.

    Niezmienna wartość, nie model bazodanowy. Operacje arytmetyczne wymagają
    tej samej waluty; mnożenie przez ułamek zaokrągla raz, ROUND_HALF_UP.
    """

    amount: int
    currency: str = DEFAULT_CURRENCY

    def __post_init__(self) -> None:
        # bool jest podklasą int — `Money(True)` to niemal na pewno pomyłka.
        if isinstance(self.amount, bool) or not isinstance(self.amount, int):
            raise TypeError(
                f"amount must be int minor units, got {type(self.amount).__name__}"
            )
        if not _CURRENCY_RE.match(self.currency):
            raise ValueError(
                f"currency must be a 3-letter ISO 4217 code, got {self.currency!r}"
            )

    @classmethod
    def zero(cls, currency: str = DEFAULT_CURRENCY) -> Money:
        return cls(0, currency)

    @classmethod
    def from_decimal(
        cls,
        value: Decimal | str | int,
        currency: str = DEFAULT_CURRENCY,
        rounding: str = ROUND_HALF_UP,
    ) -> Money:
        """Buduje kwotę z wartości w jednostce głównej (np. `"19.99"`).

        Przyjmuje str i Decimal, ale nie float — float przechodzi przez
        reprezentację binarną i `Decimal(0.1)` nie jest tym, czym wygląda.
        """
        if isinstance(value, float):
            raise TypeError("float is not an exact decimal; pass str or Decimal")
        scale = Decimal(10) ** minor_digits(currency)
        minor = (Decimal(value) * scale).quantize(Decimal(1), rounding=rounding)
        return cls(int(minor), currency)

    def to_decimal(self) -> Decimal:
        """Wartość w jednostce głównej, z dokładną liczbą miejsc po przecinku."""
        digits = minor_digits(self.currency)
        return Decimal(self.amount).scaleb(-digits).quantize(Decimal(1).scaleb(-digits))

    def multiply(self, factor: Decimal | int, rounding: str = ROUND_HALF_UP) -> Money:
        """Mnoży przez ułamek i zaokrągla dokładnie raz."""
        if isinstance(factor, float):
            raise TypeError("float factor is not exact; pass Decimal or int")
        product = (Decimal(self.amount) * Decimal(factor)).quantize(
            Decimal(1), rounding=rounding
        )
        return Money(int(product), self.currency)

    def _check_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise CurrencyMismatchError(f"{self.currency} vs {other.currency}")

    def __add__(self, other: Money) -> Money:
        self._check_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._check_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __neg__(self) -> Money:
        return Money(-self.amount, self.currency)

    def __abs__(self) -> Money:
        return Money(abs(self.amount), self.currency)

    def __mul__(self, factor: int) -> Money:
        """Mnożenie przez liczbę sztuk. Ułamek — `multiply`, żeby zaokrąglenie było jawne."""
        if isinstance(factor, bool) or not isinstance(factor, int):
            raise TypeError("use Money.multiply() for non-integer factors")
        return Money(self.amount * factor, self.currency)

    __rmul__ = __mul__

    def __bool__(self) -> bool:
        return self.amount != 0

    def __lt__(self, other: Money) -> bool:
        self._check_currency(other)
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        self._check_currency(other)
        return self.amount <= other.amount

    def __gt__(self, other: Money) -> bool:
        self._check_currency(other)
        return self.amount > other.amount

    def __ge__(self, other: Money) -> bool:
        self._check_currency(other)
        return self.amount >= other.amount

    def __str__(self) -> str:
        return f"{self.to_decimal()} {self.currency}"
