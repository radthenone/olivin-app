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
        """Filtr po materiale."""
        assert _names(api_client, material=Material.GOLD) == [
            "Łańcuszek złoty",
            "Pierścionek złoty",
        ]

    def test_fineness(self, api_client, catalog):
        """Filtr po próbie kruszcu."""
        assert _names(api_client, fineness=Fineness.F925) == ["Pierścionek srebrny"]

    def test_metal_color(self, api_client, catalog):
        """Filtr po kolorze kruszcu."""
        assert _names(api_client, metal_color=MetalColor.ROSE) == ["Łańcuszek złoty"]

    def test_stone(self, api_client, catalog):
        """Filtr po kamieniu."""
        assert _names(api_client, stone=Stone.DIAMOND) == ["Pierścionek złoty"]

    def test_size(self, api_client, catalog):
        """Filtr po rozmiarze."""
        assert _names(api_client, size=RingSize.S12) == ["Pierścionek srebrny"]

    def test_length(self, api_client, catalog):
        """Filtr po długości."""
        assert _names(api_client, length=Length.L50) == ["Łańcuszek złoty"]

    def test_filters_combine(self, api_client, catalog):
        """Filtry się sumują."""
        assert _names(api_client, material=Material.GOLD, stone=Stone.DIAMOND) == [
            "Pierścionek złoty"
        ]

    def test_unknown_value_is_error_not_ignored_filter(self, api_client, catalog):
        """Wartość spoza listy jest błędem, a nie cichym brakiem filtru."""
        response: Any = api_client.get(reverse("product-list"), {"material": "wood"})

        assert response.status_code == 400

    def test_product_with_many_matching_variants_is_listed_once(
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

    def test_leaf_returns_its_products(self, api_client, catalog):
        """Liść zwraca swoje produkty."""
        assert sorted(_names(api_client, category="engagement")) == [
            "Pierścionek srebrny",
            "Pierścionek złoty",
        ]

    def test_upper_node_includes_descendants(self, api_client, catalog):
        """Węzeł wyżej obejmuje potomków."""
        assert sorted(_names(api_client, category="rings")) == [
            "Pierścionek srebrny",
            "Pierścionek złoty",
        ]

    def test_other_branch_is_excluded(self, api_client, catalog):
        """Inna gałąź nie wchodzi."""
        assert _names(api_client, category="chains") == ["Łańcuszek złoty"]

    def test_unknown_slug_gives_empty_list_not_whole_catalog(self, api_client, catalog):
        """Nieznany slug daje pustą listę, a nie cały katalog."""
        assert _names(api_client, category="nie-ma-takiej") == []


@pytest.mark.django_db
class TestPriceFilter:
    """Cena liczy się po najtańszym wariancie produktu."""

    def test_price_min(self, api_client, catalog):
        """Dolny próg ceny."""
        assert sorted(_names(api_client, price_min=120000)) == [
            "Pierścionek złoty",
            "Łańcuszek złoty",
        ]

    def test_price_max(self, api_client, catalog):
        """Górny próg ceny."""
        assert _names(api_client, price_max=20000) == ["Pierścionek srebrny"]

    def test_range_on_both_sides(self, api_client, catalog):
        """Zakres z obu stron."""
        assert _names(api_client, price_min=100000, price_max=200000) == [
            "Łańcuszek złoty"
        ]

    def test_cheapest_variant_counts_not_any(self, api_client, catalog):
        """Produkt z wariantem za 10 zł i za 3000 zł mieści się w progu 20 zł."""
        product = PublishedProductFactory(name="Zawieszka")
        ProductVariantFactory(product=product, sku="PEN-CHEAP", price=1000)
        ProductVariantFactory(product=product, sku="PEN-RICH", price=300000)

        assert _names(api_client, price_max=2000) == ["Zawieszka"]

    def test_manual_price_counts_for_threshold(self, api_client, catalog):
        """Cena ręczna liczy się do progu."""
        product = PublishedProductFactory(name="Wyprzedaż")
        ProductVariantFactory(
            product=product, sku="SALE-1", price=300000, manual_price=1000
        )

        assert _names(api_client, price_max=2000) == ["Wyprzedaż"]

    def test_price_filter_ignores_other_filters(self, api_client, catalog):
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

    def test_newest_first_by_default(self, api_client, catalog):
        """Domyślnie od najnowszych."""
        assert _names(api_client) == [
            "Łańcuszek złoty",
            "Pierścionek srebrny",
            "Pierścionek złoty",
        ]

    def test_price_ascending(self, api_client, catalog):
        """Cena rosnąco."""
        assert _names(api_client, ordering="price") == [
            "Pierścionek srebrny",
            "Łańcuszek złoty",
            "Pierścionek złoty",
        ]

    def test_price_descending(self, api_client, catalog):
        """Cena malejąco."""
        assert _names(api_client, ordering="-price") == [
            "Pierścionek złoty",
            "Łańcuszek złoty",
            "Pierścionek srebrny",
        ]

    def test_name(self, api_client, db):
        """Nazwy z samego ASCII, bo porządek liter spoza niego rozstrzyga
        collation bazy — SQLite i PostgreSQL ustawiają „Ł" w innym miejscu."""
        for name in ("Bransoletka", "Ankra", "Cyrkonia"):
            PublishedProductFactory(name=name)

        assert _names(api_client, ordering="name") == [
            "Ankra",
            "Bransoletka",
            "Cyrkonia",
        ]

    def test_name_descending(self, api_client, db):
        """Nazwa malejąco."""
        for name in ("Bransoletka", "Ankra", "Cyrkonia"):
            PublishedProductFactory(name=name)

        assert _names(api_client, ordering="-name") == [
            "Cyrkonia",
            "Bransoletka",
            "Ankra",
        ]

    def test_newest(self, api_client, catalog):
        """Nowość."""
        assert _names(api_client, ordering="newest") == [
            "Łańcuszek złoty",
            "Pierścionek srebrny",
            "Pierścionek złoty",
        ]

    def test_product_without_variants_stays_when_sorting_by_price(
        self, api_client, catalog
    ):
        """Pusta cena — produkt bez wariantu — ląduje na końcu w obie strony,
        bo PostgreSQL i SQLite układają puste wartości w przeciwnych miejscach."""
        PublishedProductFactory(name="Bez wariantów")

        ascending = _names(api_client, ordering="price")
        descending = _names(api_client, ordering="-price")

        assert ascending[-1] == "Bez wariantów"
        assert descending[-1] == "Bez wariantów"

    def test_unknown_ordering_falls_back_to_default(self, api_client, catalog):
        """Nieznana wartość sortowania wraca do domyślnej."""
        assert _names(api_client, ordering="cokolwiek") == _names(api_client)


@pytest.mark.django_db
class TestSearch:
    """Wyszukiwarka po nazwie i opisie."""

    def test_by_name(self, api_client, catalog):
        """Wyszukiwanie po nazwie."""
        assert _names(api_client, search="Łańcuszek") == ["Łańcuszek złoty"]

    def test_by_description(self, api_client, catalog):
        """Wyszukiwanie po opisie."""
        assert _names(api_client, search="cyrkonią") == ["Pierścionek srebrny"]

    def test_phrase_without_hits_gives_empty_list(self, api_client, catalog):
        """Fraza bez trafień daje pustą listę."""
        assert _names(api_client, search="bursztyn") == []

    def test_empty_phrase_does_not_narrow_list(self, api_client, catalog):
        """Pusta fraza nie zawęża listy."""
        assert len(_names(api_client, search="   ")) == 3

    def test_search_combines_with_filter(self, api_client, catalog):
        """Szukanie łączy się z filtrem."""
        assert _names(api_client, search="Pierścionek", material=Material.GOLD) == [
            "Pierścionek złoty"
        ]

    def test_draft_is_not_in_results(self, api_client, catalog):
        """Szkic nie wpada w wyniki."""
        from tests.factories.products import ProductFactory

        ProductFactory(name="Pierścionek szkicowy")

        assert "Pierścionek szkicowy" not in _names(api_client, search="Pierścionek")


@pytest.mark.django_db
class TestParameterNamesFromTheClient:
    """Schemat ogłasza parametry w camelCase — klient wysyła je tak samo.

    Zamianę robi `CamelCaseMiddleWare`, a nie sam filtr, więc bez niego cały
    wygenerowany klient przestałby filtrować bez jednego błędu po drodze.
    """

    def test_camel_case_from_generated_client_works(self, api_client, catalog):
        """camelCase z wygenerowanego klienta działa."""
        assert _names(api_client, metalColor=MetalColor.ROSE) == ["Łańcuszek złoty"]

    def test_camel_case_in_price_threshold(self, api_client, catalog):
        """camelCase działa w progu ceny."""
        assert _names(api_client, priceMax=20000) == ["Pierścionek srebrny"]

    def test_snake_case_still_works(self, api_client, catalog):
        """snake_case nadal działa."""
        assert _names(api_client, metal_color=MetalColor.ROSE) == ["Łańcuszek złoty"]


@pytest.mark.django_db
class TestSearchEngineSeam:
    """Wybór realizacji zależy od silnika połączenia, nie od ustawień testów."""

    def test_full_text_only_on_postgres(self):
        """Pełny tekst tylko na PostgreSQL."""
        from django.db import connection

        assert supports_full_text() == (connection.vendor == "postgresql")

    def test_without_full_text_uses_substring_match(self, api_client, catalog):
        """Bez pełnego tekstu wchodzi dopasowanie po fragmencie."""
        with patch("apps.products.search.supports_full_text", return_value=False):
            assert _names(api_client, search="ańcusz") == ["Łańcuszek złoty"]


@pytest.mark.integration
@pytest.mark.django_db
class TestSearchOnPostgres:
    """Gałąź produkcyjna: pełnotekstowe wyszukiwanie PostgreSQL."""

    def test_full_text_finds_by_name(self, api_client, catalog):
        """Pełny tekst znajduje po nazwie."""
        assert supports_full_text() is True
        assert _names(api_client, search="Łańcuszek") == ["Łańcuszek złoty"]

    def test_full_text_finds_by_description(self, api_client, catalog):
        """Pełny tekst znajduje po opisie."""
        assert _names(api_client, search="pancerka") == ["Łańcuszek złoty"]
