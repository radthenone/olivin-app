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

    def test_slug_powstaje_z_angielskiego_brzmienia_nazwy(self):
        assert CollectionFactory(name="Zima").slug == "en-zima"

    def test_slug_nie_powstaje_bez_angielskiej_nazwy(self, settings):
        settings.TRANSLATION_PROVIDER = "tests.shared.translation.BrokenProvider"

        with pytest.raises(ValidationError) as error:
            CollectionFactory(name="Zima")

        assert "slug" in error.value.message_dict

    def test_wpisany_slug_zostaje_nietkniety(self):
        collection = CollectionFactory(name="Wyprzedaż zimowa", slug="winter-sale")

        assert collection.slug == "winter-sale"

    def test_kolizja_dostaje_przyrostek(self):
        CollectionFactory(name="Winter")

        assert CollectionFactory(name="Winter").slug == "en-winter-2"

    def test_zmiana_sluga_po_zapisie_jest_odrzucona(self):
        collection = CollectionFactory(name="Winter sale")

        collection.slug = "summer-sale"
        with pytest.raises(ValidationError) as error:
            collection.save()

        assert "slug" in error.value.message_dict

    def test_slug_jest_unikalny_w_bazie(self):
        CollectionFactory(slug="winter-sale")

        with pytest.raises(IntegrityError):
            Collection.objects.create(name="Inna", slug="winter-sale")


@pytest.mark.django_db
class TestMembership:
    """Kolekcja przecina kategorie; produkt należy do wielu kolekcji."""

    def test_kolekcja_laczy_produkty_z_roznych_kategorii(self):
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

    def test_produkt_nalezy_do_wielu_kolekcji(self):
        product = PublishedProductFactory()
        winter = CollectionFactory(name="Winter", products=[product])
        gifts = CollectionFactory(name="Gifts", products=[product])

        assert set(product.collections.all()) == {winter, gifts}  # type: ignore[missing-attribute]

    def test_kolekcja_moze_byc_pusta(self):
        assert CollectionFactory().products.count() == 0

    def test_skasowanie_kolekcji_nie_rusza_produktow(self):
        product = PublishedProductFactory()
        collection = CollectionFactory(products=[product])

        collection.delete()

        product.refresh_from_db()
        assert product.collections.count() == 0  # type: ignore[missing-attribute]
