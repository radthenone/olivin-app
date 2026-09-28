"""Model `Watch`: pola, status, ograniczenia (#201)."""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.watches.models import WatchKind, WatchStatus
from tests.factories.accounts import UserFactory
from tests.factories.products import MadeToOrderProductFactory, ProductVariantFactory
from tests.factories.watches import WatchFactory


@pytest.mark.django_db
class TestWatchDefaults:
    def test_active_price_drop_watch(self):
        watch = WatchFactory()

        assert watch.status == WatchStatus.ACTIVE
        assert watch.kind == WatchKind.PRICE_DROP
        assert watch.price_at_watch is not None

    def test_cascade_on_user_delete(self):
        """Anonimizacja/kasowanie konta kasuje obserwowane (issue #201)."""
        watch = WatchFactory()
        user_id = watch.user_id  # type: ignore[missing-attribute]

        watch.user.delete()

        from apps.watches.models import Watch

        assert not Watch.objects.filter(user_id=user_id).exists()


@pytest.mark.django_db
class TestMadeToOrder:
    def test_restock_rejected_for_made_to_order(self):
        from apps.watches.models import Watch

        user = UserFactory()
        product = MadeToOrderProductFactory()
        variant = ProductVariantFactory(product=product)
        watch = Watch(
            user=user, variant=variant, kind=WatchKind.RESTOCK, currency="PLN"
        )

        with pytest.raises(ValidationError):
            watch.full_clean()

    def test_price_drop_allowed_for_made_to_order(self):
        from apps.watches.services import add_watch

        user = UserFactory()
        product = MadeToOrderProductFactory()
        variant = ProductVariantFactory(product=product)

        watch = add_watch(user=user, variant=variant, kind=WatchKind.PRICE_DROP)

        assert watch.pk is not None


@pytest.mark.django_db
class TestUniqueness:
    def test_rejects_second_active_watch(self):
        watch = WatchFactory()

        with pytest.raises(IntegrityError), transaction.atomic():
            WatchFactory(user=watch.user, variant=watch.variant, kind=watch.kind)

    def test_sent_watch_frees_slot_for_new_one(self):
        from apps.watches.services import add_watch

        watch = WatchFactory()
        watch.mark_sent()

        again = add_watch(user=watch.user, variant=watch.variant, kind=watch.kind)

        assert again.status == WatchStatus.ACTIVE
