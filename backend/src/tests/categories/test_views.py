from __future__ import annotations

from typing import Any, cast

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.categories.models import Category
from tests.factories.categories import CategoryFactory


def _names(nodes: list[dict[str, Any]]) -> list[str]:
    return [node["name"] for node in nodes]


def _by_name(nodes: list[dict[str, Any]], name: str) -> dict[str, Any]:
    return next(node for node in nodes if node["name"] == name)


@pytest.mark.django_db
class TestCategoryListAccess:
    """Menu sklepu czyta każdy odwiedzający — bez logowania."""

    def test_anonim_dostaje_drzewo(self, api_client: APIClient):
        CategoryFactory(name="Biżuteria")

        response = cast(Response, api_client.get(reverse("category-list")))

        assert response.status_code == status.HTTP_200_OK

    def test_zalogowany_widzi_to_samo(
        self, authenticated_client: APIClient, api_client: APIClient
    ):
        CategoryFactory(name="Biżuteria")

        anonymous = cast(Response, api_client.get(reverse("category-list")))
        logged_in = cast(Response, authenticated_client.get(reverse("category-list")))

        assert anonymous.data == logged_in.data  # type: ignore

    def test_pojedyncza_kategoria_po_slugu(self, api_client: APIClient):
        CategoryFactory(name="Rings", slug="rings")

        response = cast(
            Response,
            api_client.get(reverse("category-detail", kwargs={"slug": "rings"})),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["slug"] == "rings"  # type: ignore

    def test_nieznany_slug_to_404(self, api_client: APIClient):
        response = cast(
            Response,
            api_client.get(reverse("category-detail", kwargs={"slug": "brak"})),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCategoryTreeShape:
    """Lista zwraca zagnieżdżone drzewo, a nie płaską listę węzłów."""

    def test_lista_zawiera_tylko_korzenie_na_najwyzszym_poziomie(
        self, api_client: APIClient
    ):
        root = CategoryFactory(name="Biżuteria")
        CategoryFactory(name="Pierścionki", parent=root)
        CategoryFactory(name="Złoto inwestycyjne")

        response = cast(Response, api_client.get(reverse("category-list")))

        assert _names(response.data) == [  # type: ignore
            "Biżuteria",
            "Złoto inwestycyjne",
        ]

    def test_potomkowie_sa_zagniezdzeni(self, api_client: APIClient):
        root = CategoryFactory(name="Biżuteria")
        rings = CategoryFactory(name="Pierścionki", parent=root)
        CategoryFactory(name="Zaręczynowe", parent=rings)

        response = cast(Response, api_client.get(reverse("category-list")))

        jewellery = _by_name(response.data, "Biżuteria")  # type: ignore
        rings_node = _by_name(jewellery["children"], "Pierścionki")
        assert _names(rings_node["children"]) == ["Zaręczynowe"]

    def test_lisc_ma_pusta_liste_potomkow(self, api_client: APIClient):
        CategoryFactory(name="Biżuteria")

        response = cast(Response, api_client.get(reverse("category-list")))

        assert response.data[0]["children"] == []  # type: ignore

    def test_szczegol_zwraca_galaz_od_wskazanego_wezla(self, api_client: APIClient):
        root = CategoryFactory(name="Biżuteria")
        rings = CategoryFactory(name="Rings", slug="rings", parent=root)
        CategoryFactory(name="Zaręczynowe", parent=rings)

        response = cast(
            Response,
            api_client.get(reverse("category-detail", kwargs={"slug": "rings"})),
        )

        assert response.data["name"] == "Rings"  # type: ignore
        assert _names(response.data["children"]) == ["Zaręczynowe"]  # type: ignore

    def test_drzewo_nie_jest_stronicowane(self, api_client: APIClient):
        for index in range(30):
            CategoryFactory(name=f"Kategoria {index:02d}")

        response = cast(Response, api_client.get(reverse("category-list")))

        assert isinstance(response.data, list)  # type: ignore
        assert len(response.data) == 30  # type: ignore

    def test_narzut_nie_wychodzi_na_zewnatrz(self, api_client: APIClient):
        CategoryFactory(name="Biżuteria", margin_percent="35.00")

        response = cast(Response, api_client.get(reverse("category-list")))

        assert set(response.data[0]) == {"id", "name", "slug", "children"}  # type: ignore

    def test_cale_drzewo_kosztuje_stala_liczbe_zapytan(
        self, api_client: APIClient, django_assert_num_queries
    ):
        root = CategoryFactory(name="Biżuteria")
        rings = CategoryFactory(name="Pierścionki", parent=root)
        CategoryFactory(name="Zaręczynowe", parent=rings)

        # Dwa zapytania: drzewo i tłumaczenia do niego. Oba stałe —
        # nie rosną wraz z liczbą węzłów.
        with django_assert_num_queries(2):
            api_client.get(reverse("category-list"))


@pytest.mark.django_db
class TestCategoryTreeSurvivesBrokenData:
    """Zapis pętli nie przepuszcza, ale `UPDATE` z pominięciem modelu już tak."""

    def test_petla_w_bazie_nie_rozklada_odczytu(self, api_client: APIClient):
        root = CategoryFactory(name="Biżuteria", slug="jewellery")
        child = CategoryFactory(name="Pierścionki", slug="rings", parent=root)
        Category.objects.filter(pk=root.pk).update(parent=child)

        response = cast(
            Response,
            api_client.get(reverse("category-detail", kwargs={"slug": "rings"})),
        )

        assert response.status_code == status.HTTP_200_OK
        assert _names(response.data["children"]) == ["Biżuteria"]  # type: ignore
        assert response.data["children"][0]["children"] == []  # type: ignore

    def test_pozostale_korzenie_zostaja_w_menu(self, api_client: APIClient):
        root = CategoryFactory(name="Biżuteria", slug="jewellery")
        child = CategoryFactory(name="Pierścionki", slug="rings", parent=root)
        CategoryFactory(name="Złoto inwestycyjne", slug="bullion")
        Category.objects.filter(pk=root.pk).update(parent=child)

        response = cast(Response, api_client.get(reverse("category-list")))

        assert _names(response.data) == ["Złoto inwestycyjne"]  # type: ignore


@pytest.mark.django_db
class TestCategoryIsReadOnly:
    """Taksonomię układa panel, nie API (ADR 0021)."""

    @pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
    def test_zapis_jest_niedozwolony(
        self, authenticated_client: APIClient, method: str
    ):
        CategoryFactory(name="Rings", slug="rings")
        url = (
            reverse("category-list")
            if method == "post"
            else reverse("category-detail", kwargs={"slug": "rings"})
        )

        response = cast(Response, getattr(authenticated_client, method)(url, {}))

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
