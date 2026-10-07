from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from apps.collections.models import Collection
from tests.factories.categories import CategoryFactory
from tests.factories.collections import CollectionFactory
from tests.factories.products import PublishedProductFactory


@pytest.mark.django_db
class TestSlug:
    """Slug jest angielskim adresem kampanii — jeden, unikalny, niezmienny."""

    def test_slug_is_built_from_english_name(self):
        """Slug powstaje z angielskiego brzmienia nazwy."""
        assert CollectionFactory(name="Zima").slug == "en-zima"

    def test_slug_is_not_built_without_english_name(self, settings):
        """Slug nie powstaje bez angielskiej nazwy."""
        settings.TRANSLATION_PROVIDER = "tests.shared.translation.BrokenProvider"

        with pytest.raises(ValidationError) as error:
            CollectionFactory(name="Zima")

        assert "slug" in error.value.message_dict

    def test_entered_slug_is_kept(self):
        """Wpisany slug zostaje nietknięty."""
        collection = CollectionFactory(name="Wyprzedaż zimowa", slug="winter-sale")

        assert collection.slug == "winter-sale"

    def test_collision_gets_suffix(self):
        """Kolizja slugów dostaje przyrostek."""
        CollectionFactory(name="Winter")

        assert CollectionFactory(name="Winter").slug == "en-winter-2"

    def test_slug_change_after_save_is_rejected(self):
        """Zmiana sluga po zapisie jest odrzucana."""
        collection = CollectionFactory(name="Winter sale")

        collection.slug = "summer-sale"
        with pytest.raises(ValidationError) as error:
            collection.save()

        assert "slug" in error.value.message_dict

    def test_slug_is_unique_in_database(self):
        """Slug jest unikalny w bazie."""
        CollectionFactory(slug="winter-sale")

        with pytest.raises(IntegrityError):
            Collection.objects.create(name="Inna", slug="winter-sale")


@pytest.mark.django_db
class TestMembership:
    """Kolekcja przecina kategorie; produkt należy do wielu kolekcji."""

    def test_collection_joins_products_from_different_categories(self):
        """Kolekcja łączy produkty z różnych kategorii."""
        rings = CategoryFactory(name="Pierścionki")
        chains = CategoryFactory(name="Łańcuszki")
        ring = PublishedProductFactory(category=rings)
        chain = PublishedProductFactory(category=chains)

        collection = CollectionFactory(products=[ring, chain])

        assert collection.products.count() == 2
        assert {product.category_id for product in collection.products.all()} == {
            rings.id,
            chains.id,
        }

    def test_product_belongs_to_many_collections(self):
        """Produkt należy do wielu kolekcji."""
        product = PublishedProductFactory()
        winter = CollectionFactory(name="Winter", products=[product])
        gifts = CollectionFactory(name="Gifts", products=[product])

        assert set(product.collections.all()) == {winter, gifts}  # type: ignore[missing-attribute]

    def test_collection_can_be_empty(self):
        """Kolekcja może być pusta."""
        assert CollectionFactory().products.count() == 0

    def test_deleting_collection_keeps_products(self):
        """Skasowanie kolekcji nie rusza produktów."""
        product = PublishedProductFactory()
        collection = CollectionFactory(products=[product])

        collection.delete()

        product.refresh_from_db()
        assert product.collections.count() == 0  # type: ignore[missing-attribute]
