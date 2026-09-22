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
class TestRezerwacjaObnizaDostepne:
    def test_rezerwacja_zdejmuje_z_dostepnosci(self):
        variant = ProductVariantFactory()
        stock(variant, 5)

        reserve(variant, 2)

        variant.refresh_from_db()
        assert variant.available == 3

    def test_stan_z_ruchow_nie_zmienia_sie_przez_rezerwacje(self):
        variant = ProductVariantFactory()
        item = stock(variant, 5)

        reserve(variant, 2)

        item.refresh_from_db()
        assert item.on_hand == 5
        assert item.reserved == 2

    def test_rezerwacja_ponad_dostepne_jest_odrzucona(self):
        variant = ProductVariantFactory()
        stock(variant, 2)

        with pytest.raises(InsufficientStock):
            reserve(variant, 3)

        assert Reservation.objects.count() == 0

    def test_dwie_rezerwacje_sumuja_sie(self):
        variant = ProductVariantFactory()
        stock(variant, 5)

        reserve(variant, 2)
        reserve(variant, 2)

        variant.refresh_from_db()
        assert variant.available == 1

    def test_druga_rezerwacja_ponad_reszte_jest_odrzucona(self):
        variant = ProductVariantFactory()
        stock(variant, 5)
        reserve(variant, 4)

        with pytest.raises(InsufficientStock):
            reserve(variant, 2)

    def test_wariant_bez_stanu_magazynowego_nie_da_sie_zarezerwowac(self):
        variant = ProductVariantFactory()

        with pytest.raises(InsufficientStock):
            reserve(variant, 1)


@pytest.mark.django_db
class TestProduktNaZamowienie:
    """Wyrób powstaje po złożeniu zamówienia — nie ma czego rezerwować (ADR 0024)."""

    def test_rezerwacja_nic_nie_tworzy(self):
        variant = ProductVariantFactory(product=MadeToOrderProductFactory())

        assert reserve(variant, 3) is None
        assert Reservation.objects.count() == 0

    def test_dostepnosc_zostaje_nieograniczona(self):
        variant = ProductVariantFactory(product=MadeToOrderProductFactory())

        reserve(variant, 99)

        variant.refresh_from_db()
        assert variant.is_available is True


@pytest.mark.django_db
class TestWygasanie:
    def test_po_trzydziestu_minutach_stan_wraca_bez_udzialu_zadania(self):
        """Suma liczy tylko rezerwacje nieprzeterminowane — spóźnione zadanie
        nie zamraża stanu."""
        variant = ProductVariantFactory()
        stock(variant, 5)
        with freeze_time(NOW):
            reserve(variant, 2)

        with freeze_time(timezone.datetime.fromisoformat(NOW) + RESERVATION_TTL):
            variant.refresh_from_db()
            assert variant.available == 5

    def test_tuz_przed_wygasnieciem_rezerwacja_dziala(self):
        variant = ProductVariantFactory()
        stock(variant, 5)
        with freeze_time(NOW):
            reserve(variant, 2)

        moment = timezone.datetime.fromisoformat(NOW) + RESERVATION_TTL
        with freeze_time(moment - timedelta(seconds=1)):
            variant.refresh_from_db()
            assert variant.available == 3

    def test_zadanie_oznacza_przeterminowane_jako_zwolnione(self):
        variant = ProductVariantFactory()
        stock(variant, 5)
        with freeze_time(NOW):
            reservation = _reserve(variant, 2)

        with freeze_time(timezone.datetime.fromisoformat(NOW) + RESERVATION_TTL):
            released = expire_reservations()  # type: ignore[missing-argument]

        assert released == 1
        reservation.refresh_from_db()
        assert reservation.status == ReservationStatus.RELEASED

    def test_zadanie_nie_rusza_swiezej_rezerwacji(self):
        variant = ProductVariantFactory()
        stock(variant, 5)
        reservation = _reserve(variant, 2)

        assert expire_reservations() == 0  # type: ignore[missing-argument]
        reservation.refresh_from_db()
        assert reservation.status == ReservationStatus.ACTIVE

    def test_zadanie_nie_rusza_rozliczonej_rezerwacji(self):
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
class TestZwolnienie:
    def test_zwolnienie_przywraca_dostepnosc(self):
        variant = ProductVariantFactory()
        stock(variant, 5)
        reservation = _reserve(variant, 2)

        release(reservation)

        variant.refresh_from_db()
        assert variant.available == 5
        assert reservation.status == ReservationStatus.RELEASED

    def test_zwolnienie_nie_rusza_stanu_z_ruchow(self):
        variant = ProductVariantFactory()
        item = stock(variant, 5)
        release(_reserve(variant, 2))

        item.refresh_from_db()
        assert item.on_hand == 5
        assert item.movements.count() == 1

    def test_zwolnienie_rozliczonej_rezerwacji_jest_odrzucone(self):
        variant = ProductVariantFactory()
        stock(variant, 5)
        reservation = _reserve(variant, 2)
        consume(reservation)

        with pytest.raises(ReservationNotActive):
            release(reservation)

    def test_zwolnienie_przeterminowanej_przechodzi(self):
        """To samo, co robi hurtem zadanie okresowe — tylko dla jednej sztuki."""
        variant = ProductVariantFactory()
        stock(variant, 5)
        with freeze_time(NOW):
            reservation = _reserve(variant, 2)

        with freeze_time(timezone.datetime.fromisoformat(NOW) + RESERVATION_TTL):
            release(reservation)

        assert reservation.status == ReservationStatus.RELEASED


@pytest.mark.django_db
class TestRozliczenie:
    """`consume()` zdejmuje towar ze stanu ruchem magazynowym, nie kolumną."""

    def test_rozliczenie_tworzy_ruch_sprzedazy(self):
        variant = ProductVariantFactory()
        item = stock(variant, 5)
        reservation = _reserve(variant, 2)

        consume(reservation)

        item.refresh_from_db()
        movement = item.movements.get(reason=StockMovementReason.SALE)
        assert movement.quantity == -2
        assert item.on_hand == 3

    def test_po_rozliczeniu_rezerwacja_przestaje_obciazac_dostepnosc(self):
        variant = ProductVariantFactory()
        stock(variant, 5)
        reservation = _reserve(variant, 2)

        consume(reservation)

        variant.refresh_from_db()
        assert reservation.status == ReservationStatus.CONSUMED
        assert variant.available == 3

    def test_rozliczenie_po_terminie_jest_odrzucone(self):
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

    def test_rozliczenie_dwa_razy_jest_odrzucone(self):
        variant = ProductVariantFactory()
        stock(variant, 5)
        reservation = _reserve(variant, 2)
        consume(reservation)

        with pytest.raises(ReservationNotActive):
            consume(reservation)

    def test_rozliczenie_zwolnionej_rezerwacji_jest_odrzucone(self):
        variant = ProductVariantFactory()
        stock(variant, 5)
        reservation = _reserve(variant, 2)
        release(reservation)

        with pytest.raises(ReservationNotActive):
            consume(reservation)


@pytest.mark.django_db
class TestSumaZamiastKolumny:
    """`InventoryItem.reserved` jest sumą aktywnych rezerwacji, nie polem."""

    def test_wlasciwosc_liczy_aktywne_rezerwacje(self):
        variant = ProductVariantFactory()
        item = stock(variant, 10)
        reserve(variant, 2)
        reserve(variant, 3)
        release(_reserve(variant, 1))

        item.refresh_from_db()
        assert item.reserved == 5

    def test_adnotacja_liczy_to_samo_co_wlasciwosc(self):
        from apps.inventory.models import AVAILABLE, RESERVED

        variant = ProductVariantFactory()
        item = stock(variant, 10)
        reserve(variant, 4)

        annotated = InventoryItem.objects.with_stock().get(pk=item.pk)

        item.refresh_from_db()
        assert getattr(annotated, RESERVED) == item.reserved
        assert getattr(annotated, AVAILABLE) == item.available
