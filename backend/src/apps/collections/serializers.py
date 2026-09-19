from __future__ import annotations

from rest_framework import serializers

from apps.collections.models import Collection


class CollectionSerializer(serializers.ModelSerializer):
    """Kolekcja na liście — bez produktów, z ich liczbą.

    Lista kolekcji służy do nawigacji, nie do pokazania katalogu: zagnieżdżenie
    produktów w każdej z nich zamieniłoby jedno żądanie w cały katalog.
    Produkty pobiera się przez `GET /products/?collection=<slug>`.
    """

    product_count = serializers.IntegerField(
        read_only=True,
        help_text="Liczba opublikowanych produktów w kolekcji",
    )

    class Meta:
        model = Collection
        fields = ["id", "name", "slug", "description", "product_count"]
        read_only_fields = fields
