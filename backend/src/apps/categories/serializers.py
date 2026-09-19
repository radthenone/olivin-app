from __future__ import annotations

from collections import defaultdict
from typing import Any

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.categories.models import Category

BY_PARENT = "categories_by_parent"


def group_by_parent(categories: list[Category]) -> dict[Any, list[Category]]:
    """Grupuje płaską listę węzłów po rodzicu.

    Drzewo składamy w pamięci z jednego zapytania — rekurencja po bazie
    dałaby zapytanie na każdy poziom menu.
    """
    grouped: dict[Any, list[Category]] = defaultdict(list)
    for category in categories:
        grouped[category.parent_id].append(category)
    return grouped


class CategorySerializer(serializers.ModelSerializer):
    """Węzeł drzewa wraz z potomkami.

    Narzut nie wychodzi na zewnątrz: to dana cenotwórcza panelu, nie treść
    katalogu.
    """

    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "children"]
        read_only_fields = fields

    @staticmethod
    def with_tree(categories: list[Category]) -> dict[str, Any]:
        """Kontekst, z którego serializer czyta potomków bez dobijania bazy."""
        return {BY_PARENT: group_by_parent(categories)}

    def get_children(self, obj: Category) -> list[dict[str, Any]]:
        # Brak kontekstu to błąd wywołania, nie przypadek do obsłużenia:
        # serializer bez pogrupowanego drzewa musiałby dobić bazę na każdym
        # węźle, a cicho zwrócona pusta lista wyglądałaby jak brak potomków.
        by_parent = self.context[BY_PARENT]
        children = by_parent.get(obj.id, [])
        return list(CategorySerializer(children, many=True, context=self.context).data)


# Pole jest rekurencyjne, więc typu nie da się podać w ciele klasy — w tym
# miejscu nazwa `CategorySerializer` jeszcze nie istnieje. Bez tej adnotacji
# drf-spectacular opisuje potomków jako wartość nieokreśloną i klient Orvala
# dostaje `unknown[]` zamiast drzewa.
CategorySerializer.get_children = extend_schema_field(  # type: ignore[method-assign]
    CategorySerializer(many=True)
)(CategorySerializer.get_children)
