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

    def test_anonymous_gets_tree(self, api_client: APIClient):
        """Anonim dostaje drzewo kategorii."""
        CategoryFactory(name="Biżuteria")

        response = cast(Response, api_client.get(reverse("category-list")))

        assert response.status_code == status.HTTP_200_OK

    def test_logged_in_sees_the_same(
        self, authenticated_client: APIClient, api_client: APIClient
    ):
        """Zalogowany widzi to samo drzewo."""
        CategoryFactory(name="Biżuteria")

        anonymous = cast(Response, api_client.get(reverse("category-list")))
        logged_in = cast(Response, authenticated_client.get(reverse("category-list")))

        assert anonymous.data == logged_in.data  # type: ignore

    def test_single_category_by_slug(self, api_client: APIClient):
        """Pojedyncza kategoria jest dostępna po slugu."""
        CategoryFactory(name="Rings", slug="rings")

        response = cast(
            Response,
            api_client.get(reverse("category-detail", kwargs={"slug": "rings"})),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["slug"] == "rings"  # type: ignore

    def test_unknown_slug_is_404(self, api_client: APIClient):
        """Nieznany slug daje 404."""
        response = cast(
            Response,
            api_client.get(reverse("category-detail", kwargs={"slug": "brak"})),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCategoryTreeShape:
    """Lista zwraca zagnieżdżone drzewo, a nie płaską listę węzłów."""

    def test_list_has_only_roots_at_top_level(self, api_client: APIClient):
        """Lista zawiera na najwyższym poziomie tylko korzenie."""
        root = CategoryFactory(name="Biżuteria")
        CategoryFactory(name="Pierścionki", parent=root)
        CategoryFactory(name="Złoto inwestycyjne")

        response = cast(Response, api_client.get(reverse("category-list")))

        assert _names(response.data) == [  # type: ignore
            "Biżuteria",
            "Złoto inwestycyjne",
        ]

    def test_children_are_nested(self, api_client: APIClient):
        """Potomkowie są zagnieżdżeni."""
        root = CategoryFactory(name="Biżuteria")
        rings = CategoryFactory(name="Pierścionki", parent=root)
        CategoryFactory(name="Zaręczynowe", parent=rings)

        response = cast(Response, api_client.get(reverse("category-list")))

        jewellery = _by_name(response.data, "Biżuteria")  # type: ignore
        rings_node = _by_name(jewellery["children"], "Pierścionki")
        assert _names(rings_node["children"]) == ["Zaręczynowe"]

    def test_leaf_has_empty_children_list(self, api_client: APIClient):
        """Liść ma pustą listę potomków."""
        CategoryFactory(name="Biżuteria")

        response = cast(Response, api_client.get(reverse("category-list")))

        assert response.data[0]["children"] == []  # type: ignore

    def test_detail_returns_branch_from_node(self, api_client: APIClient):
        """Szczegół zwraca gałąź od wskazanego węzła."""
        root = CategoryFactory(name="Biżuteria")
        rings = CategoryFactory(name="Rings", slug="rings", parent=root)
        CategoryFactory(name="Zaręczynowe", parent=rings)

        response = cast(
            Response,
            api_client.get(reverse("category-detail", kwargs={"slug": "rings"})),
        )

        assert response.data["name"] == "Rings"  # type: ignore
        assert _names(response.data["children"]) == ["Zaręczynowe"]  # type: ignore

    def test_tree_is_not_paginated(self, api_client: APIClient):
        """Drzewo nie jest stronicowane."""
        for index in range(30):
            CategoryFactory(name=f"Kategoria {index:02d}")

        response = cast(Response, api_client.get(reverse("category-list")))

        assert isinstance(response.data, list)  # type: ignore
        assert len(response.data) == 30  # type: ignore

    def test_margin_is_not_exposed(self, api_client: APIClient):
        """Narzut nie wychodzi na zewnątrz."""
        CategoryFactory(name="Biżuteria", margin_percent="35.00")

        response = cast(Response, api_client.get(reverse("category-list")))

        assert set(response.data[0]) == {"id", "name", "slug", "children"}  # type: ignore

    def test_whole_tree_costs_constant_query_count(
        self, api_client: APIClient, django_assert_num_queries
    ):
        """Całe drzewo kosztuje stałą liczbę zapytań."""
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

    def test_cycle_in_database_does_not_break_read(self, api_client: APIClient):
        """Pętla w bazie nie rozkłada odczytu."""
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

    def test_other_roots_stay_in_menu(self, api_client: APIClient):
        """Pozostałe korzenie zostają w menu."""
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
    def test_write_is_not_allowed(self, authenticated_client: APIClient, method: str):
        """Zapis przez API jest niedozwolony."""
        CategoryFactory(name="Rings", slug="rings")
        url = (
            reverse("category-list")
            if method == "post"
            else reverse("category-detail", kwargs={"slug": "rings"})
        )

        response = cast(Response, getattr(authenticated_client, method)(url, {}))

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
