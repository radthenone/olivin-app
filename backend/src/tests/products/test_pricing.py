"""Wzór ceny wariantu i przeliczenie po zatwierdzeniu kursu (ADR 0022)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.core import mail
from django.core.exceptions import ValidationError

from apps.products.models import MetalRate, MetalRateStatus, ProductVariant
from apps.products.pricing import (
    calculate_price,
    cost_floor,
    margin_for,
    round_up_to_zloty,
)
from apps.products.services import activate_rate
from apps.products.tasks import propose_metal_rates
from common.money import Money
from tests.factories.categories import CategoryFactory
from tests.factories.products import (
    CostComponentFactory,
    MetalRateFactory,
    ProductVariantFactory,
    PublishedProductFactory,
)


@pytest.fixture
def active_gold_rate(db) -> MetalRate:
    """Kurs złota próby 585: 300 zł za gram."""
    rate = MetalRateFactory(price_per_gram=30000)
    activate_rate(rate)
    rate.refresh_from_db()
    return rate


@pytest.fixture
def on_commit(django_capture_on_commit_callbacks):
    """Uruchamia to, co `activate_rate` odkłada na po zatwierdzeniu transakcji.

    Bez tego przeliczenie i wiadomość nigdy by się nie odpaliły — test siedzi
    w transakcji, która na końcu jest wycofywana, a `on_commit` czeka na
    zatwierdzenie, którego nie będzie.
    """
    return django_capture_on_commit_callbacks


def _variant(category=None, **kwargs) -> ProductVariant:
    product = PublishedProductFactory(category=category or CategoryFactory())
    return ProductVariantFactory(product=product, **kwargs)


class TestRounding:
    """Cena kończy się na pełnych złotówkach, zawsze w górę."""

    @pytest.mark.parametrize(
        ("minor_units", "expected"),
        [
            (10000, 10000),
            (10001, 10100),
            (10099, 10100),
            (1, 100),
            (0, 0),
        ],
    )
    def test_round_up(self, minor_units: int, expected: int):
        """Zaokrąglenie w górę."""
        assert round_up_to_zloty(Money(minor_units, "PLN")) == Money(expected, "PLN")


@pytest.mark.django_db
class TestFormula:
    """cena = (masa × kurs + składniki) × marża, zaokrąglone w górę."""

    def test_metal_component_only(self, active_gold_rate):
        """Sam składnik kruszcowy."""
        variant = _variant(metal_weight_grams=Decimal("2.000"))

        assert cost_floor(variant) == Money(60000, "PLN")

    def test_fractional_weight_rounds_once(self, active_gold_rate):
        """Masa ułamkowa zaokrągla się raz."""
        variant = _variant(metal_weight_grams=Decimal("3.333"))

        assert cost_floor(variant) == Money(99990, "PLN")

    def test_cost_components_are_in_floor(self, active_gold_rate):
        """Składniki kosztu wchodzą do progu."""
        variant = _variant(metal_weight_grams=Decimal("2.000"))
        CostComponentFactory(variant=variant, name="Robocizna", amount=8000)
        CostComponentFactory(variant=variant, name="Rodowanie", amount=2000)

        assert cost_floor(variant) == Money(70000, "PLN")

    def test_percent_margin(self, active_gold_rate):
        """Marża procentowa."""
        category = CategoryFactory(margin_percent=Decimal("50.00"))
        variant = _variant(category=category, metal_weight_grams=Decimal("2.000"))

        assert calculate_price(variant) == Money(90000, "PLN")

    def test_amount_margin(self, active_gold_rate):
        """Marża kwotowa."""
        category = CategoryFactory(margin_amount=15000)
        variant = _variant(category=category, metal_weight_grams=Decimal("2.000"))

        assert calculate_price(variant) == Money(75000, "PLN")

    def test_without_margin_price_equals_floor(self, active_gold_rate):
        """Bez marży cena równa się progowi."""
        variant = _variant(metal_weight_grams=Decimal("2.000"))

        assert calculate_price(variant) == cost_floor(variant)

    def test_price_is_rounded_up_after_margin(self, active_gold_rate):
        """Cena jest zaokrąglana w górę po nałożeniu marży."""
        category = CategoryFactory(margin_percent=Decimal("33.33"))
        variant = _variant(category=category, metal_weight_grams=Decimal("1.000"))

        price = calculate_price(variant)

        assert price is not None
        assert price.amount % 100 == 0
        assert price == Money(40000, "PLN")

    def test_without_active_rate_no_price_or_floor(self, db):
        """Bez aktywnego kursu nie ma ceny ani progu."""
        variant = _variant(metal_weight_grams=Decimal("2.000"))

        assert cost_floor(variant) is None
        assert calculate_price(variant) is None

    def test_proposed_rate_is_not_used(self, db):
        """Kurs zaproponowany nie liczy się do wzoru."""
        MetalRateFactory(price_per_gram=30000, status=MetalRateStatus.PROPOSED)
        variant = _variant(metal_weight_grams=Decimal("2.000"))

        assert cost_floor(variant) is None


@pytest.mark.django_db
class TestMarginInheritance:
    """Marża wariantu nadpisuje marżę kategorii."""

    def test_variant_inherits_category_margin(self, active_gold_rate):
        """Wariant dziedziczy marżę kategorii."""
        category = CategoryFactory(margin_percent=Decimal("50.00"))
        variant = _variant(category=category)

        assert margin_for(variant).percent == Decimal("50.00")

    def test_variant_margin_takes_precedence(self, active_gold_rate):
        """Marża wariantu ma pierwszeństwo."""
        category = CategoryFactory(margin_percent=Decimal("50.00"))
        variant = _variant(category=category, margin_percent=Decimal("10.00"))

        assert margin_for(variant).percent == Decimal("10.00")

    def test_variant_amount_overrides_category_percent(self, active_gold_rate):
        """Nadpisanie działa na całym narzucie, nie na pojedynczym polu —
        złożenie dwóch narzutów nie jest tym, o co prosi ADR 0022."""
        category = CategoryFactory(margin_percent=Decimal("50.00"))
        variant = _variant(category=category, margin_amount=10000)

        margin = margin_for(variant)

        assert margin.percent is None
        assert margin.amount == Money(10000, "PLN")

    def test_no_margin_anywhere_gives_empty_margin(self, active_gold_rate):
        """Brak marży wszędzie daje pusty narzut."""
        variant = _variant(category=CategoryFactory())

        assert margin_for(variant).is_empty

    def test_two_margins_on_variant_are_rejected(self, db):
        """Dwie marże na wariancie są odrzucane."""
        with pytest.raises(ValidationError):
            ProductVariantFactory(margin_percent=Decimal("10.00"), margin_amount=10000)


@pytest.mark.django_db
class TestActivation:
    """Aktywacja archiwizuje poprzedni kurs i przelicza ceny."""

    def test_activation_sets_status_and_trace(self, db, user):
        """Aktywacja ustawia status i ślad."""
        rate = MetalRateFactory()

        activate_rate(rate, activated_by=user)

        rate.refresh_from_db()
        assert rate.status == MetalRateStatus.ACTIVE
        assert rate.activated_at is not None
        assert rate.activated_by == user

    def test_previous_rate_is_archived(self, active_gold_rate):
        """Poprzedni kurs trafia do archiwum."""
        newer = MetalRateFactory(price_per_gram=35000)

        activate_rate(newer)

        active_gold_rate.refresh_from_db()
        assert active_gold_rate.status == MetalRateStatus.ARCHIVED

    def test_exactly_one_active_rate(self, active_gold_rate):
        """Aktywny kurs jest dokładnie jeden."""
        activate_rate(MetalRateFactory(price_per_gram=35000))

        assert MetalRate.objects.active().count() == 1

    def test_prices_recompute_after_activation(self, active_gold_rate, on_commit):
        """Ceny przeliczają się po aktywacji."""
        variant = _variant(metal_weight_grams=Decimal("2.000"), price=1)

        with on_commit(execute=True):
            activate_rate(MetalRateFactory(price_per_gram=35000))

        variant.refresh_from_db()
        assert variant.price == 70000

    def test_manual_price_is_untouched(self, active_gold_rate, on_commit):
        """Cena ręczna zostaje nietknięta."""
        variant = _variant(metal_weight_grams=Decimal("2.000"), manual_price=12345)

        with on_commit(execute=True):
            activate_rate(MetalRateFactory(price_per_gram=35000))

        variant.refresh_from_db()
        assert variant.manual_price == 12345
        assert variant.price == 70000

    def test_variant_of_other_metal_is_untouched(self, active_gold_rate, on_commit):
        """Wariant z innego kruszcu się nie zmienia."""
        from apps.products.models import Fineness, Material

        silver = PublishedProductFactory(
            material=Material.SILVER, fineness=Fineness.F925
        )
        variant = ProductVariantFactory(product=silver, price=4242)

        with on_commit(execute=True):
            activate_rate(MetalRateFactory(price_per_gram=35000))

        variant.refresh_from_db()
        assert variant.price == 4242

    def test_saving_rate_alone_recomputes_nothing(self, active_gold_rate):
        """Propozycja nie zmienia cen — robi to dopiero aktywacja."""
        variant = _variant(metal_weight_grams=Decimal("2.000"), price=1)

        MetalRateFactory(price_per_gram=99999, status=MetalRateStatus.PROPOSED)

        variant.refresh_from_db()
        assert variant.price == 1

    def test_owner_message_after_activation(self, active_gold_rate, user, on_commit):
        """Właściciel dostaje wiadomość po aktywacji."""
        mail.outbox.clear()

        with on_commit(execute=True):
            activate_rate(MetalRateFactory(price_per_gram=35000), activated_by=user)

        assert len(mail.outbox) == 1
        body = mail.outbox[0].body
        assert "300.00 PLN" in body
        assert "350.00 PLN" in body
        assert user.email in body

    def test_first_rate_does_not_invent_previous(self, db, user, on_commit):
        """Pierwszy kurs nie podaje fałszywego poprzedniego."""
        mail.outbox.clear()

        with on_commit(execute=True):
            activate_rate(MetalRateFactory(), activated_by=user)

        assert "Poprzedniego kursu nie było" in mail.outbox[0].body


@pytest.mark.django_db
class TestManualPriceFloor:
    """Cena ręczna nie schodzi poniżej kosztu bez marży (ADR 0022)."""

    def test_below_floor_is_rejected(self, active_gold_rate):
        """Cena poniżej progu jest odrzucana."""
        variant = _variant(metal_weight_grams=Decimal("2.000"))
        variant.manual_price = 100

        with pytest.raises(ValidationError) as error:
            variant.full_clean()

        assert "manual_price" in error.value.message_dict

    def test_exactly_at_floor_passes(self, active_gold_rate):
        """Cena równa progowi przechodzi."""
        variant = _variant(metal_weight_grams=Decimal("2.000"))
        variant.manual_price = 60000

        variant.full_clean()

    def test_above_floor_passes(self, active_gold_rate):
        """Cena powyżej progu przechodzi."""
        variant = _variant(metal_weight_grams=Decimal("2.000"))
        variant.manual_price = 80000

        variant.full_clean()

    def test_without_rate_floor_does_not_block_save(self, db):
        """Wariant zakładany przed ustaleniem kursu nie może się o to rozbić."""
        variant = _variant(metal_weight_grams=Decimal("2.000"))
        variant.manual_price = 1

        variant.full_clean()


@pytest.mark.django_db
class TestProposeTask:
    """Zadanie okresowe wstawia propozycje, nie zmienia cen."""

    def test_fallback_adapter_repeats_last_active_rate(self, active_gold_rate):
        """Dostawca nie jest wybrany (ADR 0027), więc propozycja identyczna
        z obowiązującą jest pomijana, a nie zapisywana bez treści."""
        created = propose_metal_rates()  # type: ignore[missing-argument]

        assert created == 0

    def test_without_active_rate_nothing_to_propose(self, db):
        """Bez aktywnego kursu nie ma czego proponować."""
        assert propose_metal_rates() == 0  # type: ignore[missing-argument]

    def test_proposal_does_not_change_prices(self, active_gold_rate):
        """Propozycja nie zmienia cen."""
        variant = _variant(metal_weight_grams=Decimal("2.000"), price=1)

        propose_metal_rates()  # type: ignore[missing-argument]

        variant.refresh_from_db()
        assert variant.price == 1
