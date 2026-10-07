"""Serwis ulubionych: dodanie/usunięcie idempotentne i scalenie listy gościa (#200)."""

from __future__ import annotations

import pytest

from apps.favorites.models import Favorite
from apps.favorites.services import (
    add_favorite,
    favorites_for,
    merge_favorites,
    remove_favorite,
)
from tests.factories.accounts import UserFactory
from tests.factories.favorites import FavoriteFactory
from tests.factories.products import ProductFactory, PublishedProductFactory


@pytest.mark.django_db
class TestAddFavorite:
    """Dodanie do ulubionych jest idempotentne."""

    def test_creates_favorite(self):
        """Dodanie zakłada wpis ulubionych."""
        user = UserFactory()
        product = PublishedProductFactory()

        favorite = add_favorite(user=user, product=product)

        assert favorite.user == user
        assert favorite.product == product
        assert Favorite.objects.filter(user=user, product=product).count() == 1

    def test_repeating_add_does_not_duplicate(self):
        """Powtórne dodanie nie dubluje wpisu."""
        user = UserFactory()
        product = PublishedProductFactory()
        add_favorite(user=user, product=product)

        add_favorite(user=user, product=product)

        assert Favorite.objects.filter(user=user, product=product).count() == 1


@pytest.mark.django_db
class TestRemoveFavorite:
    """Usunięcie z ulubionych jest idempotentne."""

    def test_removes_existing_favorite(self):
        """Usunięcie kasuje istniejący wpis."""
        favorite = FavoriteFactory()

        remove_favorite(
            user=favorite.user,
            product_slug=favorite.product.slug,  # type: ignore[bad-argument-type]
        )

        assert not Favorite.objects.filter(pk=favorite.pk).exists()

    def test_removing_missing_favorite_is_not_an_error(self):
        """Usunięcie nieistniejącego wpisu nie jest błędem."""
        user = UserFactory()
        product = PublishedProductFactory()

        remove_favorite(
            user=user,
            product_slug=product.slug,  # type: ignore[bad-argument-type]
        )  # brak wpisu — brak błędu

        assert not Favorite.objects.filter(user=user, product=product).exists()


@pytest.mark.django_db
class TestFavoritesFor:
    """Lista w API pomija produkty nieopublikowane, ale nie kasuje rekordu."""

    def test_lists_only_published_products(self):
        """Lista obejmuje tylko produkty opublikowane."""
        user = UserFactory()
        published = FavoriteFactory(user=user, product=PublishedProductFactory())
        draft_favorite = FavoriteFactory(user=user, product=ProductFactory())

        favorites = list(favorites_for(user))

        assert favorites == [published]
        assert Favorite.objects.filter(pk=draft_favorite.pk).exists()


@pytest.mark.django_db
class TestMergeFavorites:
    """Scalenie listy gościa (slugi produktów) z listą konta."""

    def test_merges_new_products_into_account_list(self):
        """Nowe produkty gościa trafiają na listę konta."""
        user = UserFactory()
        existing = PublishedProductFactory()
        FavoriteFactory(user=user, product=existing)
        guest_product = PublishedProductFactory()

        merged = merge_favorites(
            user=user,
            product_slugs=[guest_product.slug, existing.slug],  # type: ignore[bad-argument-type]
        )

        products = {favorite.product for favorite in merged}
        assert products == {existing, guest_product}

    def test_skips_nonexistent_and_unpublished_slugs(self):
        """Nieistniejące i nieopublikowane slugi są pomijane."""
        user = UserFactory()
        draft = ProductFactory()

        merged = merge_favorites(
            user=user,
            product_slugs=[draft.slug, "brak-takiego"],  # type: ignore[bad-argument-type]
        )

        assert list(merged) == []
        assert not Favorite.objects.filter(user=user).exists()

    def test_repeating_merge_is_idempotent(self):
        """Powtórne scalenie niczego nie zmienia."""
        user = UserFactory()
        product = PublishedProductFactory()
        merge_favorites(user=user, product_slugs=[product.slug])  # type: ignore[bad-argument-type]

        merge_favorites(user=user, product_slugs=[product.slug])  # type: ignore[bad-argument-type]

        assert Favorite.objects.filter(user=user, product=product).count() == 1

    def test_duplicate_slugs_in_input_do_not_duplicate_favorite(self):
        """Duplikaty w liście gościa są odsiewane przed zapytaniem — jedna
        pozycja `IN (...)`, jeden wpis ulubionych."""
        user = UserFactory()
        product = PublishedProductFactory()

        merged = merge_favorites(
            user=user,
            product_slugs=[product.slug, product.slug],  # type: ignore[bad-argument-type]
        )

        assert Favorite.objects.filter(user=user, product=product).count() == 1
        assert list(merged) == list(Favorite.objects.filter(user=user))
