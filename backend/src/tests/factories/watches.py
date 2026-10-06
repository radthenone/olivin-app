from __future__ import annotations

from factory.declarations import SubFactory
from factory.django import DjangoModelFactory

from apps.watches.models import Watch, WatchKind, WatchStatus
from tests.factories.accounts import UserFactory
from tests.factories.products import ProductVariantFactory


class WatchFactory(DjangoModelFactory):
    """Aktywna prośba o powiadomienie o spadku ceny."""

    class Meta:
        model = Watch

    user = SubFactory(UserFactory)
    variant = SubFactory(ProductVariantFactory)
    kind = WatchKind.PRICE_DROP
    price_at_watch = 129900
    currency = "PLN"
    status = WatchStatus.ACTIVE
