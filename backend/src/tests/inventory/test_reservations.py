"""Rezerwacja stanu na czas płatności (`CONTEXT.md`, Reservation)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone
from freezegun import freeze_time

from apps.inventory.models import (
    RESERVATION_TTL,
    InventoryItem,
    Reservation,
    ReservationStatus,
    StockMovementReason,
)
from apps.inventory.services import (
    InsufficientStock,
    ReservationNotActive,
    consume,
    release,
    reserve,
)
from apps.inventory.tasks import expire_reservations
from tests.factories.inventory import ReservationFactory
from tests.factories.products import (
    MadeToOrderProductFactory,
    ProductVariantFactory,
    stock,
)

NOW = "2026-09-22 10:00:00"


def _reserve(variant, quantity: int) -> Reservation:
    """`reserve()` zwraca `None` dla wyrobu na zamówienie — tu zawsze jest rezerwacja."""
    reservation = reserve(variant, quantity)
    assert reservation is not None
    return reservation


@pytest.mark.django_db
class TestReservationReducesAvailability:
    """Rezerwacja obniża dostępność wariantu."""

    def test_reservation_reduces_availability(self):
        """Rezerwacja zdejmuje sztuki z dostępności."""
        variant = ProductVariantFactory()
        stock(variant, 5)

        reserve(variant, 2)

        variant.refresh_from_db()
        assert variant.available == 3

    def test_stock_from_movements_is_unchanged(self):
        """Stan z ruchów nie zmienia się przez rezerwację."""
        variant = ProductVariantFactory()
        item = stock(variant, 5)

        reserve(variant, 2)

        item.refresh_from_db()
        assert item.on_hand == 5
        assert item.reserved == 2

    def test_reservation_above_available_is_rejected(self):
        """Rezerwacja ponad dostępne sztuki jest odrzucana."""
        variant = ProductVariantFactory()
        stock(variant, 2)

        with pytest.raises(InsufficientStock):
            reserve(variant, 3)

        assert Reservation.objects.count() == 0

    def test_two_reservations_add_up(self):
        """Dwie rezerwacje sumują się."""
        variant = ProductVariantFactory()
        stock(variant, 5)

        reserve(variant, 2)
        reserve(variant, 2)

        variant.refresh_from_db()
        assert variant.available == 1

    def test_second_reservation_above_rest_is_rejected(self):
        """Druga rezerwacja ponad resztę jest odrzucana."""
        variant = ProductVariantFactory()
        stock(variant, 5)
        reserve(variant, 4)

        with pytest.raises(InsufficientStock):
            reserve(variant, 2)

    def test_variant_without_inventory_cannot_be_reserved(self):
        """Wariantu bez stanu magazynowego nie da się zarezerwować."""
        variant = ProductVariantFactory()

        with pytest.raises(InsufficientStock):
            reserve(variant, 1)


@pytest.mark.django_db
class TestMadeToOrderProduct:
    """Wyrób powstaje po złożeniu zamówienia — nie ma czego rezerwować (ADR 0024)."""

    def test_reservation_creates_nothing(self):
        """Rezerwacja niczego nie tworzy."""
        variant = ProductVariantFactory(product=MadeToOrderProductFactory())

        assert reserve(variant, 3) is None
        assert Reservation.objects.count() == 0

    def test_availability_stays_unlimited(self):
        """Dostępność zostaje nieograniczona."""
        variant = ProductVariantFactory(product=MadeToOrderProductFactory())

        reserve(variant, 99)

        variant.refresh_from_db()
        assert variant.is_available is True


@pytest.mark.django_db
class TestExpiry:
    """Rezerwacja wygasa po trzydziestu minutach."""

    def test_stock_returns_after_thirty_minutes_without_task(self):
        """Suma liczy tylko rezerwacje nieprzeterminowane — spóźnione zadanie
        nie zamraża stanu."""
        variant = ProductVariantFactory()
        stock(variant, 5)
        with freeze_time(NOW):
            reserve(variant, 2)

        with freeze_time(timezone.datetime.fromisoformat(NOW) + RESERVATION_TTL):
            variant.refresh_from_db()
            assert variant.available == 5

    def test_reservation_holds_right_before_expiry(self):
        """Tuż przed wygaśnięciem rezerwacja działa."""
        variant = ProductVariantFactory()
        stock(variant, 5)
        with freeze_time(NOW):
            reserve(variant, 2)

        moment = timezone.datetime.fromisoformat(NOW) + RESERVATION_TTL
        with freeze_time(moment - timedelta(seconds=1)):
            variant.refresh_from_db()
            assert variant.available == 3

    def test_task_marks_expired_as_released(self):
        """Zadanie oznacza przeterminowane rezerwacje jako zwolnione."""
        variant = ProductVariantFactory()
        stock(variant, 5)
        with freeze_time(NOW):
            reservation = _reserve(variant, 2)

        with freeze_time(timezone.datetime.fromisoformat(NOW) + RESERVATION_TTL):
            released = expire_reservations()  # type: ignore[missing-argument]

        assert released == 1
        reservation.refresh_from_db()
        assert reservation.status == ReservationStatus.RELEASED

    def test_task_keeps_fresh_reservation(self):
        """Zadanie nie rusza świeżej rezerwacji."""
        variant = ProductVariantFactory()
        stock(variant, 5)
        reservation = _reserve(variant, 2)

        assert expire_reservations() == 0  # type: ignore[missing-argument]
        reservation.refresh_from_db()
        assert reservation.status == ReservationStatus.ACTIVE

    def test_task_keeps_consumed_reservation(self):
        """Zadanie nie rusza rozliczonej rezerwacji."""
        variant = ProductVariantFactory()
        stock(variant, 5)
        reservation = ReservationFactory(
            variant=variant,
            quantity=2,
            status=ReservationStatus.CONSUMED,
            expires_at=timezone.now() - timedelta(hours=1),
        )

        expire_reservations()  # type: ignore[missing-argument]

        reservation.refresh_from_db()
        assert reservation.status == ReservationStatus.CONSUMED


@pytest.mark.django_db
class TestRelease:
    """Zwolnienie rezerwacji."""

    def test_release_restores_availability(self):
        """Zwolnienie przywraca dostępność."""
        variant = ProductVariantFactory()
        stock(variant, 5)
        reservation = _reserve(variant, 2)

        release(reservation)

        variant.refresh_from_db()
        assert variant.available == 5
        assert reservation.status == ReservationStatus.RELEASED

    def test_release_keeps_stock_from_movements(self):
        """Zwolnienie nie rusza stanu z ruchów."""
        variant = ProductVariantFactory()
        item = stock(variant, 5)
        release(_reserve(variant, 2))

        item.refresh_from_db()
        assert item.on_hand == 5
        assert item.movements.count() == 1

    def test_release_of_consumed_reservation_is_rejected(self):
        """Zwolnienie rozliczonej rezerwacji jest odrzucane."""
        variant = ProductVariantFactory()
        stock(variant, 5)
        reservation = _reserve(variant, 2)
        consume(reservation)

        with pytest.raises(ReservationNotActive):
            release(reservation)

    def test_release_of_expired_reservation_passes(self):
        """Zwolnienie przeterminowanej rezerwacji przechodzi.

        To samo, co robi hurtem zadanie okresowe — tylko dla jednej sztuki.
        """
        variant = ProductVariantFactory()
        stock(variant, 5)
        with freeze_time(NOW):
            reservation = _reserve(variant, 2)

        with freeze_time(timezone.datetime.fromisoformat(NOW) + RESERVATION_TTL):
            release(reservation)

        assert reservation.status == ReservationStatus.RELEASED


@pytest.mark.django_db
class TestConsume:
    """`consume()` zdejmuje towar ze stanu ruchem magazynowym, nie kolumną."""

    def test_consume_creates_sale_movement(self):
        """Rozliczenie tworzy ruch sprzedaży."""
        variant = ProductVariantFactory()
        item = stock(variant, 5)
        reservation = _reserve(variant, 2)

        consume(reservation)

        item.refresh_from_db()
        movement = item.movements.get(reason=StockMovementReason.SALE)
        assert movement.quantity == -2
        assert item.on_hand == 3

    def test_consumed_reservation_no_longer_reduces_availability(self):
        """Po rozliczeniu rezerwacja przestaje obciążać dostępność."""
        variant = ProductVariantFactory()
        stock(variant, 5)
        reservation = _reserve(variant, 2)

        consume(reservation)

        variant.refresh_from_db()
        assert reservation.status == ReservationStatus.CONSUMED
        assert variant.available == 3

    def test_consume_after_expiry_is_rejected(self):
        """Stan wrócił do sprzedaży i mógł zejść komu innemu — drugie zdjęcie
        zeszłoby poniżej zera."""
        variant = ProductVariantFactory()
        item = stock(variant, 1)
        with freeze_time(NOW):
            reservation = _reserve(variant, 1)

        with freeze_time(timezone.datetime.fromisoformat(NOW) + RESERVATION_TTL):
            with pytest.raises(ReservationNotActive):
                consume(reservation)

        item.refresh_from_db()
        assert item.on_hand == 1

    def test_consume_twice_is_rejected(self):
        """Dwukrotne rozliczenie jest odrzucane."""
        variant = ProductVariantFactory()
        stock(variant, 5)
        reservation = _reserve(variant, 2)
        consume(reservation)

        with pytest.raises(ReservationNotActive):
            consume(reservation)

    def test_consume_of_released_reservation_is_rejected(self):
        """Rozliczenie zwolnionej rezerwacji jest odrzucane."""
        variant = ProductVariantFactory()
        stock(variant, 5)
        reservation = _reserve(variant, 2)
        release(reservation)

        with pytest.raises(ReservationNotActive):
            consume(reservation)


@pytest.mark.django_db
class TestSumInsteadOfColumn:
    """`InventoryItem.reserved` jest sumą aktywnych rezerwacji, nie polem."""

    def test_property_counts_active_reservations(self):
        """Właściwość liczy aktywne rezerwacje."""
        variant = ProductVariantFactory()
        item = stock(variant, 10)
        reserve(variant, 2)
        reserve(variant, 3)
        release(_reserve(variant, 1))

        item.refresh_from_db()
        assert item.reserved == 5

    def test_annotation_matches_property(self):
        """Adnotacja liczy to samo co właściwość."""
        from apps.inventory.models import AVAILABLE, RESERVED

        variant = ProductVariantFactory()
        item = stock(variant, 10)
        reserve(variant, 4)

        annotated = InventoryItem.objects.with_stock().get(pk=item.pk)

        item.refresh_from_db()
        assert getattr(annotated, RESERVED) == item.reserved
        assert getattr(annotated, AVAILABLE) == item.available
