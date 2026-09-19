"""Filtrowanie, sortowanie i wyszukiwanie listy produktów."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.products.models import Fineness, Length, Material, MetalColor, RingSize, Stone
from apps.products.search import supports_full_text
from tests.factories.categories import CategoryFactory
from tests.factories.products import ProductVariantFactory, PublishedProductFactory


def _names(client, **params: Any) -> list[str]:
    response: Any = client.get(reverse("product-list"), params or None)
    assert response.status_code == 200, response.content
    return [row["name"] for row in response.json()["results"]]


@pytest.fixture
def catalog(db):
    """Mały katalog, w którym każda cecha różni dokładnie jedną parę."""
    rings = CategoryFactory(name="Pierścionki", slug="rings")
    engagement = CategoryFactory(name="Zaręczynowe", slug="engagement", parent=rings)
    chains = CategoryFactory(name="Łańcuszki", slug="chains")

    gold_ring = PublishedProductFactory(
        name="Pierścionek złoty",
        description="Klasyczna obrączka z żółtego złota",
        category=engagement,
        material=Material.GOLD,
        fineness=Fineness.F585,
    )
    ProductVariantFactory(
        product=gold_ring,
        sku="RING-GOLD",
        metal_color=MetalColor.YELLOW,
        size=RingSize.S16,
        stone=Stone.DIAMOND,
        price=250000,
    )

    silver_ring = PublishedProductFactory(
        name="Pierścionek srebrny",
        description="Delikatny pierścionek z cyrkonią",
        category=engagement,
        material=Material.SILVER,
        fineness=Fineness.F925,
    )
    ProductVariantFactory(
        product=silver_ring,
        sku="RING-SILVER",
        metal_color=MetalColor.WHITE,
        size=RingSize.S12,
        stone=Stone.CUBIC_ZIRCONIA,
        price=19900,
    )

    chain = PublishedProductFactory(
        name="Łańcuszek złoty",
        description="Splot pancerka, długość pięćdziesiąt centymetrów",
        category=chains,
        material=Material.GOLD,
        fineness=Fineness.F750,
    )
    ProductVariantFactory(
        product=chain,
        sku="CHAIN-GOLD",
        metal_color=MetalColor.ROSE,
        length=Length.L50,
        price=120000,
    )

    return {"rings": rings, "engagement": engagement, "chains": chains}


@pytest.mark.django_db
class TestFeatureFilters:
    """Każda cecha zawęża listę do produktów, które ją mają."""

    def test_material(self, api_client, catalog):
        assert _names(api_client, material=Material.GOLD) == [
            "Łańcuszek złoty",
            "Pierścionek złoty",
        ]

    def test_fineness(self, api_client, catalog):
        assert _names(api_client, fineness=Fineness.F925) == ["Pierścionek srebrny"]

    def test_metal_color(self, api_client, catalog):
        assert _names(api_client, metal_color=MetalColor.ROSE) == ["Łańcuszek złoty"]

    def test_stone(self, api_client, catalog):
        assert _names(api_client, stone=Stone.DIAMOND) == ["Pierścionek złoty"]

    def test_size(self, api_client, catalog):
        assert _names(api_client, size=RingSize.S12) == ["Pierścionek srebrny"]

    def test_length(self, api_client, catalog):
        assert _names(api_client, length=Length.L50) == ["Łańcuszek złoty"]

    def test_filtry_sie_sumuja(self, api_client, catalog):
        assert _names(api_client, material=Material.GOLD, stone=Stone.DIAMOND) == [
            "Pierścionek złoty"
        ]

    def test_wartosc_spoza_listy_jest_bledem_a_nie_cichym_brakiem_filtru(
        self, api_client, catalog
    ):
        response: Any = api_client.get(reverse("product-list"), {"material": "wood"})

        assert response.status_code == 400

    def test_produkt_z_wieloma_pasujacymi_wariantami_wraca_raz(
        self, api_client, catalog
    ):
        """Filtr po cesze wariantu idzie przez złączenie — bez `distinct`
        produkt z dwoma pasującymi wariantami pojawiłby się dwa razy."""
        product = PublishedProductFactory(name="Kolczyki")
        for index in range(2):
            ProductVariantFactory(
                product=product,
                sku=f"EAR-{index}",
                metal_color=MetalColor.BICOLOR,
                price=50000 + index,
            )

        assert _names(api_client, metal_color=MetalColor.BICOLOR) == ["Kolczyki"]


@pytest.mark.django_db
class TestCategoryFilter:
    """Kategoria obejmuje swoje podkategorie — klient klika w węzeł, nie w liść."""

    def test_lisc_zwraca_swoje_produkty(self, api_client, catalog):
        assert sorted(_names(api_client, category="engagement")) == [
            "Pierścionek srebrny",
            "Pierścionek złoty",
        ]

    def test_wezel_wyzej_obejmuje_potomkow(self, api_client, catalog):
        assert sorted(_names(api_client, category="rings")) == [
            "Pierścionek srebrny",
            "Pierścionek złoty",
        ]

    def test_inna_galaz_nie_wchodzi(self, api_client, catalog):
        assert _names(api_client, category="chains") == ["Łańcuszek złoty"]

    def test_nieznany_slug_daje_pusta_liste_a_nie_caly_katalog(
        self, api_client, catalog
    ):
        assert _names(api_client, category="nie-ma-takiej") == []


@pytest.mark.django_db
class TestPriceFilter:
    """Cena liczy się po najtańszym wariancie produktu."""

    def test_price_min(self, api_client, catalog):
        assert sorted(_names(api_client, price_min=120000)) == [
            "Pierścionek złoty",
            "Łańcuszek złoty",
        ]

    def test_price_max(self, api_client, catalog):
        assert _names(api_client, price_max=20000) == ["Pierścionek srebrny"]

    def test_zakres_z_obu_stron(self, api_client, catalog):
        assert _names(api_client, price_min=100000, price_max=200000) == [
            "Łańcuszek złoty"
        ]

    def test_liczy_sie_najtanszy_wariant_a_nie_dowolny(self, api_client, catalog):
        """Produkt z wariantem za 10 zł i za 3000 zł mieści się w progu 20 zł."""
        product = PublishedProductFactory(name="Zawieszka")
        ProductVariantFactory(product=product, sku="PEN-CHEAP", price=1000)
        ProductVariantFactory(product=product, sku="PEN-RICH", price=300000)

        assert _names(api_client, price_max=2000) == ["Zawieszka"]

    def test_cena_reczna_liczy_sie_do_progu(self, api_client, catalog):
        product = PublishedProductFactory(name="Wyprzedaż")
        ProductVariantFactory(
            product=product, sku="SALE-1", price=300000, manual_price=1000
        )

        assert _names(api_client, price_max=2000) == ["Wyprzedaż"]

    def test_filtr_ceny_nie_zmienia_sie_od_innych_filtrow(self, api_client, catalog):
        """Cena produktu to najtańszy wariant w ogóle, a nie najtańszy
        z tych, które przeszły filtr cechy."""
        product = PublishedProductFactory(name="Bransoletka")
        ProductVariantFactory(
            product=product,
            sku="BRA-CHEAP",
            metal_color=MetalColor.YELLOW,
            price=1000,
        )
        ProductVariantFactory(
            product=product,
            sku="BRA-RICH",
            metal_color=MetalColor.WHITE,
            price=300000,
        )

        found = _names(api_client, metal_color=MetalColor.WHITE, price_max=2000)

        assert found == ["Bransoletka"]


@pytest.mark.django_db
class TestOrdering:
    """Sortowanie: cena rosnąco i malejąco, nowość, nazwa."""

    def test_domyslnie_od_najnowszych(self, api_client, catalog):
        assert _names(api_client) == [
            "Łańcuszek złoty",
            "Pierścionek srebrny",
            "Pierścionek złoty",
        ]

    def test_cena_rosnaco(self, api_client, catalog):
        assert _names(api_client, ordering="price") == [
            "Pierścionek srebrny",
            "Łańcuszek złoty",
            "Pierścionek złoty",
        ]

    def test_cena_malejaco(self, api_client, catalog):
        assert _names(api_client, ordering="-price") == [
            "Pierścionek złoty",
            "Łańcuszek złoty",
            "Pierścionek srebrny",
        ]

    def test_nazwa(self, api_client, db):
        """Nazwy z samego ASCII, bo porządek liter spoza niego rozstrzyga
        collation bazy — SQLite i PostgreSQL ustawiają „Ł" w innym miejscu."""
        for name in ("Bransoletka", "Ankra", "Cyrkonia"):
            PublishedProductFactory(name=name)

        assert _names(api_client, ordering="name") == [
            "Ankra",
            "Bransoletka",
            "Cyrkonia",
        ]

    def test_nazwa_malejaco(self, api_client, db):
        for name in ("Bransoletka", "Ankra", "Cyrkonia"):
            PublishedProductFactory(name=name)

        assert _names(api_client, ordering="-name") == [
            "Cyrkonia",
            "Bransoletka",
            "Ankra",
        ]

    def test_nowosc(self, api_client, catalog):
        assert _names(api_client, ordering="newest") == [
            "Łańcuszek złoty",
            "Pierścionek srebrny",
            "Pierścionek złoty",
        ]

    def test_produkt_bez_wariantow_nie_wypada_z_listy_przy_sortowaniu_po_cenie(
        self, api_client, catalog
    ):
        """Pusta cena — produkt bez wariantu — ląduje na końcu w obie strony,
        bo PostgreSQL i SQLite układają puste wartości w przeciwnych miejscach."""
        PublishedProductFactory(name="Bez wariantów")

        rosnaco = _names(api_client, ordering="price")
        malejaco = _names(api_client, ordering="-price")

        assert rosnaco[-1] == "Bez wariantów"
        assert malejaco[-1] == "Bez wariantów"

    def test_nieznana_wartosc_sortowania_wraca_do_domyslnej(self, api_client, catalog):
        assert _names(api_client, ordering="cokolwiek") == _names(api_client)


@pytest.mark.django_db
class TestSearch:
    """Wyszukiwarka po nazwie i opisie."""

    def test_po_nazwie(self, api_client, catalog):
        assert _names(api_client, search="Łańcuszek") == ["Łańcuszek złoty"]

    def test_po_opisie(self, api_client, catalog):
        assert _names(api_client, search="cyrkonią") == ["Pierścionek srebrny"]

    def test_fraza_bez_trafien_daje_pusta_liste(self, api_client, catalog):
        assert _names(api_client, search="bursztyn") == []

    def test_pusta_fraza_nie_zaweza_listy(self, api_client, catalog):
        assert len(_names(api_client, search="   ")) == 3

    def test_szukanie_laczy_sie_z_filtrem(self, api_client, catalog):
        assert _names(api_client, search="Pierścionek", material=Material.GOLD) == [
            "Pierścionek złoty"
        ]

    def test_szkic_nie_wpada_w_wyniki(self, api_client, catalog):
        from tests.factories.products import ProductFactory

        ProductFactory(name="Pierścionek szkicowy")

        assert "Pierścionek szkicowy" not in _names(api_client, search="Pierścionek")


@pytest.mark.django_db
class TestParameterNamesFromTheClient:
    """Schemat ogłasza parametry w camelCase — klient wysyła je tak samo.

    Zamianę robi `CamelCaseMiddleWare`, a nie sam filtr, więc bez niego cały
    wygenerowany klient przestałby filtrować bez jednego błędu po drodze.
    """

    def test_camel_case_z_wygenerowanego_klienta_dziala(self, api_client, catalog):
        assert _names(api_client, metalColor=MetalColor.ROSE) == ["Łańcuszek złoty"]

    def test_camel_case_w_progu_ceny(self, api_client, catalog):
        assert _names(api_client, priceMax=20000) == ["Pierścionek srebrny"]

    def test_snake_case_nadal_dziala(self, api_client, catalog):
        assert _names(api_client, metal_color=MetalColor.ROSE) == ["Łańcuszek złoty"]


@pytest.mark.django_db
class TestSearchEngineSeam:
    """Wybór realizacji zależy od silnika połączenia, nie od ustawień testów."""

    def test_pelny_tekst_tylko_na_postgresie(self):
        from django.db import connection

        assert supports_full_text() == (connection.vendor == "postgresql")

    def test_bez_pelnego_tekstu_wchodzi_dopasowanie_po_fragmencie(
        self, api_client, catalog
    ):
        with patch("apps.products.search.supports_full_text", return_value=False):
            assert _names(api_client, search="ańcusz") == ["Łańcuszek złoty"]


@pytest.mark.integration
@pytest.mark.django_db
class TestSearchOnPostgres:
    """Gałąź produkcyjna: pełnotekstowe wyszukiwanie PostgreSQL."""

    def test_pelny_tekst_znajduje_po_nazwie(self, api_client, catalog):
        assert supports_full_text() is True
        assert _names(api_client, search="Łańcuszek") == ["Łańcuszek złoty"]

    def test_pelny_tekst_znajduje_po_opisie(self, api_client, catalog):
        assert _names(api_client, search="pancerka") == ["Łańcuszek złoty"]
