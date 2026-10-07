"""Serwis obserwowanych: oba wyzwalacze, zgoda marketingowa, wygaśnięcie (#201)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from apps.notifications.models import Notification, NotificationPreference
from apps.watches.models import WatchKind, WatchStatus
from apps.watches.services import (
    add_watch,
    notify_price_watches,
    notify_restock_watches,
)
from tests.factories.accounts import UserFactory
from tests.factories.products import (
    InventoryItemFactory,
    ProductVariantFactory,
    StockMovementFactory,
)
from tests.factories.inventory import ReservationFactory  # noqa: F401
from apps.inventory.models import StockMovementReason
from tests.factories.watches import WatchFactory


def _stocked_variant(quantity: int):
    """Wariant z ruchem dostawy na `quantity` sztuk."""
    item = InventoryItemFactory()
    StockMovementFactory(
        item=item, quantity=quantity, reason=StockMovementReason.DELIVERY
    )
    variant = item.variant
    variant.refresh_from_db()
    return variant


@pytest.mark.django_db
class TestAddWatch:
    """Dodanie obserwacji."""

    def test_price_drop_saves_current_price(self):
        """Obserwacja spadku ceny zapamiętuje bieżącą cenę."""
        user = UserFactory()
        variant = ProductVariantFactory(price=129900)

        watch = add_watch(user=user, variant=variant, kind=WatchKind.PRICE_DROP)

        assert watch.price_at_watch == variant.effective_price.amount

    def test_repeating_add_returns_existing(self):
        """Powtórne dodanie zwraca istniejącą obserwację."""
        user = UserFactory()
        variant = ProductVariantFactory(price=129900)
        first = add_watch(user=user, variant=variant, kind=WatchKind.PRICE_DROP)

        second = add_watch(user=user, variant=variant, kind=WatchKind.PRICE_DROP)

        assert second.pk == first.pk

    def test_restock_rejected_for_made_to_order(self):
        """Powrót na stan jest odrzucany dla produktu na zamówienie."""
        from django.core.exceptions import ValidationError

        from tests.factories.products import MadeToOrderProductFactory

        user = UserFactory()
        variant = ProductVariantFactory(product=MadeToOrderProductFactory())

        with pytest.raises(ValidationError):
            add_watch(user=user, variant=variant, kind=WatchKind.RESTOCK)


@pytest.mark.django_db
class TestRestockTrigger:
    """Powiadomienie o powrocie na stan."""

    def test_sends_when_availability_goes_above_zero(
        self, django_capture_on_commit_callbacks
    ):
        """Powiadomienie idzie, gdy dostępność rośnie powyżej zera."""
        user = UserFactory()
        NotificationPreference.objects.create(user=user, marketing_email=True)
        variant = ProductVariantFactory()
        watch = add_watch(user=user, variant=variant, kind=WatchKind.RESTOCK)
        assert (variant.available or 0) == 0

        item = InventoryItemFactory(variant=variant)
        with patch("apps.notifications.services.send_notification_email"):
            with django_capture_on_commit_callbacks(execute=True):
                StockMovementFactory(
                    item=item, quantity=2, reason=StockMovementReason.DELIVERY
                )

        watch.refresh_from_db()
        assert watch.status == WatchStatus.SENT
        assert Notification.objects.filter(user=user).count() == 1

    def test_no_send_while_still_unavailable(self):
        """Bez dostępności nie ma powiadomienia."""
        user = UserFactory()
        NotificationPreference.objects.create(user=user, marketing_email=True)
        variant = ProductVariantFactory()
        watch = add_watch(user=user, variant=variant, kind=WatchKind.RESTOCK)

        sent = notify_restock_watches(variant)

        assert sent == 0
        watch.refresh_from_db()
        assert watch.status == WatchStatus.ACTIVE

    def test_no_consent_leaves_watch_active(self, django_capture_on_commit_callbacks):
        """Bez zgody obserwacja zostaje aktywna."""
        user = UserFactory()
        NotificationPreference.objects.create(user=user, marketing_email=False)
        variant = ProductVariantFactory()
        watch = add_watch(user=user, variant=variant, kind=WatchKind.RESTOCK)

        _stocked_variant_on(item_variant=variant, quantity=3)

        watch.refresh_from_db()
        assert watch.status == WatchStatus.ACTIVE
        assert Notification.objects.filter(user=user).count() == 0

    def test_one_shot_second_restock_sends_nothing(self):
        """Drugi powrót na stan niczego nie wysyła."""
        user = UserFactory()
        NotificationPreference.objects.create(user=user, marketing_email=True)
        variant = _stocked_variant(2)
        WatchFactory(
            user=user, variant=variant, kind=WatchKind.RESTOCK, price_at_watch=None
        )
        assert notify_restock_watches(variant) == 1
        assert notify_restock_watches(variant) == 0


def _stocked_variant_on(*, item_variant, quantity: int):
    from apps.inventory.models import InventoryItem

    item, _ = InventoryItem.objects.get_or_create(variant=item_variant)
    StockMovementFactory(
        item=item, quantity=quantity, reason=StockMovementReason.DELIVERY
    )


@pytest.mark.django_db
class TestPriceDropTrigger:
    """Powiadomienie o spadku ceny."""

    def test_sends_when_price_drops(self):
        """Powiadomienie idzie, gdy cena spada."""
        user = UserFactory()
        NotificationPreference.objects.create(user=user, marketing_email=True)
        variant = ProductVariantFactory(price=129900)
        watch = add_watch(user=user, variant=variant, kind=WatchKind.PRICE_DROP)

        variant.price = 99900
        variant.save(update_fields=["price", "updated_at"])

        sent = notify_price_watches(variant)

        assert sent == 1
        watch.refresh_from_db()
        assert watch.status == WatchStatus.SENT
        stored = Notification.objects.get(user=user)
        assert stored.kind == "watch_price_drop"

    def test_no_send_when_price_same_or_higher(self):
        """Ta sama albo wyższa cena nie wysyła powiadomienia."""
        user = UserFactory()
        NotificationPreference.objects.create(user=user, marketing_email=True)
        variant = ProductVariantFactory(price=100000)
        watch = add_watch(user=user, variant=variant, kind=WatchKind.PRICE_DROP)

        variant.price = 120000
        variant.save(update_fields=["price", "updated_at"])

        assert notify_price_watches(variant) == 0
        watch.refresh_from_db()
        assert watch.status == WatchStatus.ACTIVE

    def test_no_consent_leaves_watch_active(self):
        """Bez zgody obserwacja zostaje aktywna."""
        user = UserFactory()
        NotificationPreference.objects.create(user=user, marketing_email=False)
        variant = ProductVariantFactory(price=129900)
        watch = add_watch(user=user, variant=variant, kind=WatchKind.PRICE_DROP)

        variant.price = 99900
        variant.save(update_fields=["price", "updated_at"])

        assert notify_price_watches(variant) == 0
        watch.refresh_from_db()
        assert watch.status == WatchStatus.ACTIVE
        assert Notification.objects.filter(user=user).count() == 0

    def test_manual_price_drop_triggers(self):
        """Cena ręczna ma pierwszeństwo — jej obniżka też budzi Watch."""
        user = UserFactory()
        NotificationPreference.objects.create(user=user, marketing_email=True)
        variant = ProductVariantFactory(price=129900, manual_price=129900)
        watch = add_watch(user=user, variant=variant, kind=WatchKind.PRICE_DROP)

        variant.manual_price = 89900
        variant.save()

        assert notify_price_watches(variant) == 1
        watch.refresh_from_db()
        assert watch.status == WatchStatus.SENT
