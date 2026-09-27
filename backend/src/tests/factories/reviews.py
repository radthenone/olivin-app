from __future__ import annotations

from factory.declarations import SubFactory
from factory.django import DjangoModelFactory

from apps.reviews.models import Review, ReviewStatus
from tests.factories.accounts import UserFactory
from tests.factories.products import PublishedProductFactory


class ReviewFactory(DjangoModelFactory):
    """Opinia klienta o produkcie — domyślnie zaakceptowana, żeby widać ją było publicznie."""

    class Meta:
        model = Review

    product = SubFactory(PublishedProductFactory)
    user = SubFactory(UserFactory)
    rating = 5
    comment = "Świetny produkt"
    status = ReviewStatus.APPROVED
