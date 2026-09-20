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
        ("grosze", "expected"),
        [
            (10000, 10000),
            (10001, 10100),
            (10099, 10100),
            (1, 100),
            (0, 0),
        ],
    )
    def test_zaokraglenie_w_gore(self, grosze: int, expected: int):
        assert round_up_to_zloty(Money(grosze, "PLN")) == Money(expected, "PLN")


@pytest.mark.django_db
class TestFormula:
    """cena = (masa × kurs + składniki) × marża, zaokrąglone w górę."""

    def test_sam_skladnik_kruszcowy(self, active_gold_rate):
        variant = _variant(metal_weight_grams=Decimal("2.000"))

        assert cost_floor(variant) == Money(60000, "PLN")

    def test_masa_ulamkowa_zaokragla_sie_raz(self, active_gold_rate):
        variant = _variant(metal_weight_grams=Decimal("3.333"))

        assert cost_floor(variant) == Money(99990, "PLN")

    def test_skladniki_kosztu_wchodza_do_progu(self, active_gold_rate):
        variant = _variant(metal_weight_grams=Decimal("2.000"))
        CostComponentFactory(variant=variant, name="Robocizna", amount=8000)
        CostComponentFactory(variant=variant, name="Rodowanie", amount=2000)

        assert cost_floor(variant) == Money(70000, "PLN")

    def test_marza_procentowa(self, active_gold_rate):
        category = CategoryFactory(margin_percent=Decimal("50.00"))
        variant = _variant(category=category, metal_weight_grams=Decimal("2.000"))

        assert calculate_price(variant) == Money(90000, "PLN")

    def test_marza_kwotowa(self, active_gold_rate):
        category = CategoryFactory(margin_amount=15000)
        variant = _variant(category=category, metal_weight_grams=Decimal("2.000"))

        assert calculate_price(variant) == Money(75000, "PLN")

    def test_bez_marzy_cena_rowna_sie_progowi(self, active_gold_rate):
        variant = _variant(metal_weight_grams=Decimal("2.000"))

        assert calculate_price(variant) == cost_floor(variant)

    def test_cena_jest_zaokraglana_w_gore_po_nalozeniu_marzy(self, active_gold_rate):
        category = CategoryFactory(margin_percent=Decimal("33.33"))
        variant = _variant(category=category, metal_weight_grams=Decimal("1.000"))

        price = calculate_price(variant)

        assert price is not None
        assert price.amount % 100 == 0
        assert price == Money(40000, "PLN")

    def test_bez_aktywnego_kursu_nie_ma_ceny_ani_progu(self, db):
        variant = _variant(metal_weight_grams=Decimal("2.000"))

        assert cost_floor(variant) is None
        assert calculate_price(variant) is None

    def test_kurs_zaproponowany_nie_liczy_sie_do_wzoru(self, db):
        MetalRateFactory(price_per_gram=30000, status=MetalRateStatus.PROPOSED)
        variant = _variant(metal_weight_grams=Decimal("2.000"))

        assert cost_floor(variant) is None


@pytest.mark.django_db
class TestMarginInheritance:
    """Marża wariantu nadpisuje marżę kategorii."""

    def test_wariant_dziedziczy_marze_kategorii(self, active_gold_rate):
        category = CategoryFactory(margin_percent=Decimal("50.00"))
        variant = _variant(category=category)

        assert margin_for(variant).percent == Decimal("50.00")

    def test_marza_wariantu_ma_pierwszenstwo(self, active_gold_rate):
        category = CategoryFactory(margin_percent=Decimal("50.00"))
        variant = _variant(category=category, margin_percent=Decimal("10.00"))

        assert margin_for(variant).percent == Decimal("10.00")

    def test_kwotowa_na_wariancie_wypiera_procentowa_z_kategorii(
        self, active_gold_rate
    ):
        """Nadpisanie działa na całym narzucie, nie na pojedynczym polu —
        złożenie dwóch narzutów nie jest tym, o co prosi ADR 0022."""
        category = CategoryFactory(margin_percent=Decimal("50.00"))
        variant = _variant(category=category, margin_amount=10000)

        margin = margin_for(variant)

        assert margin.percent is None
        assert margin.amount == Money(10000, "PLN")

    def test_brak_marzy_wszedzie_daje_narzut_pusty(self, active_gold_rate):
        variant = _variant(category=CategoryFactory())

        assert margin_for(variant).is_empty

    def test_dwie_marze_na_wariancie_sa_odrzucone(self, db):
        with pytest.raises(ValidationError):
            ProductVariantFactory(margin_percent=Decimal("10.00"), margin_amount=10000)


@pytest.mark.django_db
class TestActivation:
    """Aktywacja archiwizuje poprzedni kurs i przelicza ceny."""

    def test_aktywacja_ustawia_status_i_slad(self, db, user):
        rate = MetalRateFactory()

        activate_rate(rate, activated_by=user)

        rate.refresh_from_db()
        assert rate.status == MetalRateStatus.ACTIVE
        assert rate.activated_at is not None
        assert rate.activated_by == user

    def test_poprzedni_kurs_trafia_do_archiwum(self, active_gold_rate):
        newer = MetalRateFactory(price_per_gram=35000)

        activate_rate(newer)

        active_gold_rate.refresh_from_db()
        assert active_gold_rate.status == MetalRateStatus.ARCHIVED

    def test_aktywny_kurs_jest_dokladnie_jeden(self, active_gold_rate):
        activate_rate(MetalRateFactory(price_per_gram=35000))

        assert MetalRate.objects.active().count() == 1

    def test_ceny_przeliczaja_sie_po_aktywacji(self, active_gold_rate, on_commit):
        variant = _variant(metal_weight_grams=Decimal("2.000"), price=1)

        with on_commit(execute=True):
            activate_rate(MetalRateFactory(price_per_gram=35000))

        variant.refresh_from_db()
        assert variant.price == 70000

    def test_cena_reczna_zostaje_nietknieta(self, active_gold_rate, on_commit):
        variant = _variant(metal_weight_grams=Decimal("2.000"), manual_price=12345)

        with on_commit(execute=True):
            activate_rate(MetalRateFactory(price_per_gram=35000))

        variant.refresh_from_db()
        assert variant.manual_price == 12345
        assert variant.price == 70000

    def test_wariant_z_innego_kruszcu_nie_rusza_sie(self, active_gold_rate, on_commit):
        from apps.products.models import Fineness, Material

        silver = PublishedProductFactory(
            material=Material.SILVER, fineness=Fineness.F925
        )
        variant = ProductVariantFactory(product=silver, price=4242)

        with on_commit(execute=True):
            activate_rate(MetalRateFactory(price_per_gram=35000))

        variant.refresh_from_db()
        assert variant.price == 4242

    def test_sam_zapis_kursu_niczego_nie_przelicza(self, active_gold_rate):
        """Propozycja nie zmienia cen — robi to dopiero aktywacja."""
        variant = _variant(metal_weight_grams=Decimal("2.000"), price=1)

        MetalRateFactory(price_per_gram=99999, status=MetalRateStatus.PROPOSED)

        variant.refresh_from_db()
        assert variant.price == 1

    def test_wiadomosc_do_wlasciciela_po_aktywacji(
        self, active_gold_rate, user, on_commit
    ):
        mail.outbox.clear()

        with on_commit(execute=True):
            activate_rate(MetalRateFactory(price_per_gram=35000), activated_by=user)

        assert len(mail.outbox) == 1
        body = mail.outbox[0].body
        assert "300.00 PLN" in body
        assert "350.00 PLN" in body
        assert user.email in body

    def test_pierwszy_kurs_nie_klamie_o_poprzednim(self, db, user, on_commit):
        mail.outbox.clear()

        with on_commit(execute=True):
            activate_rate(MetalRateFactory(), activated_by=user)

        assert "Poprzedniego kursu nie było" in mail.outbox[0].body


@pytest.mark.django_db
class TestManualPriceFloor:
    """Cena ręczna nie schodzi poniżej kosztu bez marży (ADR 0022)."""

    def test_ponizej_progu_jest_odrzucona(self, active_gold_rate):
        variant = _variant(metal_weight_grams=Decimal("2.000"))
        variant.manual_price = 100

        with pytest.raises(ValidationError) as error:
            variant.full_clean()

        assert "manual_price" in error.value.message_dict

    def test_rowno_na_progu_przechodzi(self, active_gold_rate):
        variant = _variant(metal_weight_grams=Decimal("2.000"))
        variant.manual_price = 60000

        variant.full_clean()

    def test_powyzej_progu_przechodzi(self, active_gold_rate):
        variant = _variant(metal_weight_grams=Decimal("2.000"))
        variant.manual_price = 80000

        variant.full_clean()

    def test_bez_kursu_prog_nie_blokuje_zapisu(self, db):
        """Wariant zakładany przed ustaleniem kursu nie może się o to rozbić."""
        variant = _variant(metal_weight_grams=Decimal("2.000"))
        variant.manual_price = 1

        variant.full_clean()


@pytest.mark.django_db
class TestProposeTask:
    """Zadanie okresowe wstawia propozycje, nie zmienia cen."""

    def test_adapter_zastepczy_powtarza_ostatni_aktywny_kurs(self, active_gold_rate):
        """Dostawca nie jest wybrany (ADR 0027), więc propozycja identyczna
        z obowiązującą jest pomijana, a nie zapisywana bez treści."""
        created = propose_metal_rates()  # type: ignore[missing-argument]

        assert created == 0

    def test_bez_aktywnego_kursu_nie_ma_czego_proponowac(self, db):
        assert propose_metal_rates() == 0  # type: ignore[missing-argument]

    def test_propozycja_nie_zmienia_cen(self, active_gold_rate):
        variant = _variant(metal_weight_grams=Decimal("2.000"), price=1)

        propose_metal_rates()  # type: ignore[missing-argument]

        variant.refresh_from_db()
        assert variant.price == 1
