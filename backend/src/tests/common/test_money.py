from __future__ import annotations

from decimal import ROUND_DOWN, Decimal

import pytest

from common.money import (
    CurrencyMismatchError,
    Money,
    allocate,
    split_evenly,
    split_gross,
)

pytestmark = pytest.mark.unit


class TestMoneyConstruction:
    """Tworzenie kwoty `Money`."""

    def test_default_currency_is_pln(self):
        """Domyślna waluta to PLN."""
        assert Money(100).currency == "PLN"

    def test_rejects_float_amount(self):
        """Kwota typu float jest odrzucana."""
        with pytest.raises(TypeError):
            Money(1.5)  # type: ignore[arg-type]

    def test_rejects_bool_amount(self):
        """Kwota typu bool jest odrzucana."""
        with pytest.raises(TypeError):
            Money(True)

    def test_rejects_malformed_currency(self):
        """Niepoprawny kod waluty jest odrzucany."""
        with pytest.raises(ValueError):
            Money(1, "pln")

    def test_from_decimal_string_rounds_half_up(self):
        """`from_decimal` zaokrągla połówki w górę."""
        assert Money.from_decimal("19.995") == Money(2000)
        assert Money.from_decimal("19.994") == Money(1999)

    def test_from_decimal_honours_rounding_mode(self):
        """`from_decimal` stosuje podany tryb zaokrąglania."""
        assert Money.from_decimal("19.999", rounding=ROUND_DOWN) == Money(1999)

    def test_from_decimal_rejects_float(self):
        """`from_decimal` odrzuca float."""
        with pytest.raises(TypeError):
            Money.from_decimal(19.99)  # type: ignore[arg-type]

    def test_to_decimal_keeps_two_places(self):
        """`to_decimal` zachowuje dwa miejsca po przecinku."""
        assert Money(1999).to_decimal() == Decimal("19.99")
        assert str(Money(1999).to_decimal()) == "19.99"
        assert str(Money(500).to_decimal()) == "5.00"

    def test_zero_minor_digit_currency(self):
        """Waluta bez części ułamkowej działa poprawnie."""
        assert Money.from_decimal("1500", "JPY") == Money(1500, "JPY")
        assert str(Money(1500, "JPY").to_decimal()) == "1500"

    def test_is_immutable(self):
        """`Money` jest niezmienne."""
        with pytest.raises(AttributeError):
            Money(1).amount = 2  # type: ignore[misc]


class TestMoneyArithmetic:
    """Działania na kwotach."""

    def test_add_and_subtract(self):
        """Dodawanie i odejmowanie kwot."""
        assert Money(100) + Money(50) == Money(150)
        assert Money(100) - Money(150) == Money(-50)

    def test_currency_mismatch_raises(self):
        """Różne waluty w działaniu dają błąd."""
        with pytest.raises(CurrencyMismatchError):
            Money(1, "PLN") + Money(1, "EUR")
        with pytest.raises(CurrencyMismatchError):
            Money(1, "PLN") < Money(1, "EUR")

    def test_multiply_by_quantity(self):
        """Mnożenie przez liczbę sztuk."""
        assert Money(1999) * 3 == Money(5997)
        assert 3 * Money(1999) == Money(5997)

    def test_star_rejects_fractions(self):
        """Operator `*` odrzuca ułamki."""
        with pytest.raises(TypeError):
            Money(100) * Decimal("0.5")  # type: ignore[operator]

    def test_multiply_rounds_once_half_up(self):
        # 1.235 zł * 0.5 = 61.75 gr -> 62 gr; przy podwójnym zaokrągleniu byłoby 61 lub 62 zależnie od ścieżki
        """Mnożenie zaokrągla raz, połówki w górę."""
        assert Money(1235).multiply(Decimal("0.5")) == Money(618)
        assert Money(1).multiply(Decimal("0.5")) == Money(1)

    def test_multiply_rejects_float(self):
        """Mnożenie odrzuca float."""
        with pytest.raises(TypeError):
            Money(100).multiply(0.5)  # type: ignore[arg-type]

    def test_comparisons_and_truthiness(self):
        """Porównania i wartość logiczna kwot."""
        assert Money(1) > Money(0)
        assert Money(0) <= Money(0)
        assert not Money.zero()
        assert Money(-1)

    def test_neg_and_abs(self):
        """Negacja i wartość bezwzględna."""
        assert -Money(5) == Money(-5)
        assert abs(Money(-5)) == Money(5)

    def test_str(self):
        """Tekstowa postać kwoty."""
        assert str(Money(1999)) == "19.99 PLN"


class TestAllocate:
    """Podział kwoty na części."""

    def test_parts_sum_exactly_to_total(self):
        """Części sumują się dokładnie do całości."""
        parts = allocate(Money(1000), [1, 1, 1])
        assert sum(p.amount for p in parts) == 1000

    def test_remainder_goes_to_last_position(self):
        """Reszta z zaokrąglenia trafia do ostatniej pozycji."""
        assert allocate(Money(1000), [1, 1, 1]) == [Money(333), Money(333), Money(334)]

    def test_proportional_to_ratios(self):
        # rabat 10 zł na koszyk 30 zł + 70 zł
        """Podział jest proporcjonalny do wag."""
        assert allocate(Money(1000), [3000, 7000]) == [Money(300), Money(700)]

    def test_zero_ratio_gets_nothing(self):
        """Waga zerowa nie dostaje nic."""
        assert allocate(Money(100), [0, 1]) == [Money(0), Money(100)]

    def test_negative_total_keeps_sign_and_sums(self):
        """Ujemna całość zachowuje znak i sumę."""
        parts = allocate(Money(-1000), [1, 1, 1])
        assert parts == [Money(-333), Money(-333), Money(-334)]
        assert sum(p.amount for p in parts) == -1000

    def test_split_evenly(self):
        """Podział na równe części."""
        assert split_evenly(Money(101), 2) == [Money(50), Money(51)]

    @pytest.mark.parametrize("ratios", [[], [0, 0], [1, -1]])
    def test_rejects_degenerate_ratios(self, ratios):
        """Zdegenerowane wagi są odrzucane."""
        with pytest.raises(ValueError):
            allocate(Money(100), ratios)

    def test_rejects_non_positive_count(self):
        """Liczba części musi być dodatnia."""
        with pytest.raises(ValueError):
            split_evenly(Money(100), 0)


class TestSplitGross:
    """Rozbicie kwoty brutto na netto i podatek."""

    def test_standard_rate(self):
        """Stawka podstawowa."""
        breakdown = split_gross(Money(12300), Decimal("0.23"))
        assert breakdown.net == Money(10000)
        assert breakdown.tax == Money(2300)

    def test_net_plus_tax_always_equals_gross(self):
        """Netto plus podatek zawsze równa się brutto."""
        for gross in range(1, 2000):
            breakdown = split_gross(Money(gross), Decimal("0.23"))
            assert breakdown.net + breakdown.tax == breakdown.gross

    def test_rounds_net_half_up(self):
        # 100 gr / 1.23 = 81.30... -> 81 ; podatek 19
        """Netto jest zaokrąglane połówką w górę."""
        breakdown = split_gross(Money(100), Decimal("0.23"))
        assert (breakdown.net, breakdown.tax) == (Money(81), Money(19))

    def test_zero_rate_means_no_tax(self):
        """Stawka zerowa oznacza brak podatku."""
        breakdown = split_gross(Money(999), Decimal("0"))
        assert breakdown.net == Money(999)
        assert breakdown.tax == Money(0)

    def test_rejects_float_and_negative_rate(self):
        """Stawka typu float albo ujemna jest odrzucana."""
        with pytest.raises(TypeError):
            split_gross(Money(100), 0.23)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            split_gross(Money(100), Decimal("-0.1"))

    def test_keeps_currency(self):
        """Wynik zachowuje walutę."""
        assert split_gross(Money(100, "EUR"), Decimal("0.19")).net.currency == "EUR"
