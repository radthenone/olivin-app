from __future__ import annotations

from collections import defaultdict
from typing import Any

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.categories.models import Category
from apps.translations.serializers import TranslatedCharField

BY_PARENT = "categories_by_parent"
VISITED = "categories_visited"


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

    name = TranslatedCharField()
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
        # W drzewie każdy węzeł ma jednego rodzica, więc wspólny zbiór
        # odwiedzonych nie przytnie niczego poprawnego. Chroni za to przed
        # rozłożeniem rekurencji, gdyby pętla weszła do bazy z pominięciem
        # modelu — zapis jej nie przepuszcza, ale `UPDATE` już tak.
        visited = self.context.setdefault(VISITED, set())
        visited.add(obj.id)
        children = [
            node for node in by_parent.get(obj.id, []) if node.id not in visited
        ]
        return list(CategorySerializer(children, many=True, context=self.context).data)


# Pole jest rekurencyjne, więc typu nie da się podać w ciele klasy — w tym
# miejscu nazwa `CategorySerializer` jeszcze nie istnieje. Bez tej adnotacji
# drf-spectacular opisuje potomków jako wartość nieokreśloną, a wygenerowany
# interfejs TypeScriptu dostaje `unknown[]` zamiast drzewa. Schemat Zod i tak
# zostaje przy `unknown` — orval nie potrafi zapisać typu rekurencyjnego
# w tamtym wyjściu.
CategorySerializer.get_children = extend_schema_field(  # type: ignore[method-assign]
    CategorySerializer(many=True)
)(CategorySerializer.get_children)
