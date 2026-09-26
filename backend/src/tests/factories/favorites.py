from __future__ import annotations

from factory.declarations import SubFactory
from factory.django import DjangoModelFactory

from apps.favorites.models import Favorite
from tests.factories.accounts import UserFactory
from tests.factories.products import PublishedProductFactory


class FavoriteFactory(DjangoModelFactory):
    """Wpis ulubionych — domyślnie produkt opublikowany."""

    class Meta:
        model = Favorite

    user = SubFactory(UserFactory)
    product = SubFactory(PublishedProductFactory)
