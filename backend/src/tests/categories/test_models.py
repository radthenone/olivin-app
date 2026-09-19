from __future__ import annotations

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from apps.categories.models import Category
from common.money import Money
from tests.factories.categories import CategoryFactory


@pytest.mark.django_db
class TestSlug:
    """Slug jest angielskim adresem kategorii — jeden, unikalny, niezmienny."""

    def test_pusty_slug_powstaje_z_nazwy(self):
        category = CategoryFactory(name="Gold rings")

        assert category.slug == "gold-rings"

    def test_wpisany_slug_zostaje_nietkniety(self):
        category = CategoryFactory(name="Pierścionki złote", slug="gold-rings")

        assert category.slug == "gold-rings"

    def test_kolizja_dostaje_przyrostek(self):
        CategoryFactory(name="Gold rings")
        second = CategoryFactory(name="Gold rings")

        assert second.slug == "gold-rings-2"

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("Łańcuszki", "lancuszki"),
            ("Pierścionki złote", "pierscionki-zlote"),
            ("ŁAŃCUSZKI", "lancuszki"),
            ("Kolczyki żółte", "kolczyki-zolte"),
        ],
    )
    def test_polskie_litery_nie_wypadaja_z_adresu(self, name: str, expected: str):
        """`slugify` nie rozkłada „ł" — bez podmiany zostaje `ancuszki`,
        a slug jest niezmienny, więc literówka zostałaby na stałe."""
        assert CategoryFactory(name=name).slug == expected

    def test_nazwa_bez_znakow_slugowalnych_nie_zostawia_pustego_adresu(self):
        category = CategoryFactory(name="✦✦✦")

        assert category.slug == "category"

    def test_zmiana_sluga_po_zapisie_jest_odrzucona(self):
        category = CategoryFactory(name="Gold rings")

        category.slug = "silver-rings"
        with pytest.raises(ValidationError) as error:
            category.save()

        assert "slug" in error.value.message_dict

    def test_zapis_bez_zmiany_sluga_przechodzi(self):
        category = CategoryFactory(name="Gold rings")

        category.name = "Złote pierścionki"
        category.save()

        category.refresh_from_db()
        assert category.slug == "gold-rings"
        assert category.name == "Złote pierścionki"

    def test_slug_jest_unikalny_w_bazie(self):
        CategoryFactory(slug="gold-rings")

        with pytest.raises(IntegrityError):
            Category.objects.create(name="Inne", slug="gold-rings")


@pytest.mark.django_db
class TestTree:
    """Drzewo jest listą sąsiedztwa: rodzic opcjonalny, potomkowie przez relację."""

    def test_kategoria_bez_rodzica_jest_korzeniem(self):
        root = CategoryFactory(name="Biżuteria")

        assert root.parent is None
        assert list(Category.objects.filter(parent__isnull=True)) == [root]

    def test_potomkowie_sa_dostepni_przez_relacje(self):
        root = CategoryFactory(name="Biżuteria")
        child = CategoryFactory(name="Pierścionki", parent=root)

        assert list(Category.objects.filter(parent=root)) == [child]
        assert child.parent == root

    def test_drzewo_ma_wiele_poziomow(self):
        root = CategoryFactory(name="Biżuteria")
        middle = CategoryFactory(name="Pierścionki", parent=root)
        leaf = CategoryFactory(name="Zaręczynowe", parent=middle)

        assert leaf.parent is not None
        assert leaf.parent.parent == root

    def test_kategoria_nie_moze_byc_swoim_rodzicem(self):
        category = CategoryFactory(name="Biżuteria")

        category.parent = category
        with pytest.raises(ValidationError) as error:
            category.full_clean()

        assert "parent" in error.value.message_dict

    def test_petla_w_drzewie_jest_odrzucona(self):
        root = CategoryFactory(name="Biżuteria")
        child = CategoryFactory(name="Pierścionki", parent=root)

        root.parent = child
        with pytest.raises(ValidationError) as error:
            root.full_clean()

        assert "parent" in error.value.message_dict

    def test_petla_nie_przechodzi_takze_przez_sam_zapis(self):
        """`save()` nie woła `clean()`, a pętla to uszkodzenie danych:
        gałąź bez korzenia wypada z menu i rozkłada rekurencję przy odczycie."""
        root = CategoryFactory(name="Biżuteria")
        child = CategoryFactory(name="Pierścionki", parent=root)

        root.parent = child
        with pytest.raises(ValidationError) as error:
            root.save()

        assert "parent" in error.value.message_dict

    def test_kategoria_nie_zostanie_swoim_rodzicem_przez_zapis(self):
        category = CategoryFactory(name="Biżuteria")

        category.parent = category
        with pytest.raises(ValidationError):
            category.save()

    def test_glebokie_drzewo_zapisuje_sie_bez_falszywego_alarmu(self):
        node = CategoryFactory(name="Poziom 0")
        for depth in range(1, 12):
            node = CategoryFactory(name=f"Poziom {depth}", parent=node)

        node.name = "Poziom ostatni"
        node.save()

        assert Category.objects.count() == 12

    def test_kategoria_z_potomkami_nie_znika_po_cichu(self):
        from django.db.models import ProtectedError

        root = CategoryFactory(name="Biżuteria")
        CategoryFactory(name="Pierścionki", parent=root)

        with pytest.raises(ProtectedError):
            root.delete()


@pytest.mark.django_db
class TestMargin:
    """Narzut domyślny kategorii: procent albo kwota, nigdy oba (ADR 0022)."""

    def test_narzut_procentowy(self):
        category = CategoryFactory(margin_percent=Decimal("35.00"))

        assert category.margin_percent == Decimal("35.00")
        assert category.margin is None

    def test_narzut_kwotowy_jest_pieniedzmi(self):
        category = CategoryFactory(margin_amount=15000)

        assert category.margin == Money(15000, "PLN")

    def test_brak_narzutu_jest_dozwolony(self):
        category = CategoryFactory()

        assert category.margin_percent is None
        assert category.margin is None

    def test_oba_narzuty_naraz_sa_odrzucone_w_walidacji(self):
        category = CategoryFactory.build(
            margin_percent=Decimal("35.00"), margin_amount=15000
        )

        with pytest.raises(ValidationError) as error:
            category.full_clean()

        assert "margin_amount" in error.value.message_dict

    def test_oba_narzuty_naraz_sa_odrzucone_przez_baze(self):
        with pytest.raises(IntegrityError):
            Category.objects.create(
                name="Obrączki",
                margin_percent=Decimal("35.00"),
                margin_amount=15000,
            )
