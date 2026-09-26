"""Model `Favorite`: unikalna para użytkownik+produkt (#200)."""

from __future__ import annotations

import pytest
from django.db import IntegrityError, transaction

from tests.factories.accounts import UserFactory
from tests.factories.favorites import FavoriteFactory
from tests.factories.products import PublishedProductFactory


@pytest.mark.django_db
class TestFavoriteUniqueness:
    """Para użytkownik+produkt jest unikalna w bazie."""

    def test_rejects_duplicate_pair(self):
        user = UserFactory()
        product = PublishedProductFactory()
        FavoriteFactory(user=user, product=product)

        with pytest.raises(IntegrityError), transaction.atomic():
            FavoriteFactory(user=user, product=product)

    def test_same_product_allowed_for_different_users(self):
        product = PublishedProductFactory()
        FavoriteFactory(product=product)
        FavoriteFactory(product=product)  # inny użytkownik z fabryki — bez błędu
