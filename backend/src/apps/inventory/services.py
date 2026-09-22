from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.inventory.models import (
    RESERVATION_TTL,
    InventoryItem,
    Reservation,
    ReservationStatus,
    StockMovement,
    StockMovementReason,
)
from apps.products.models import ProductVariant


class InsufficientStock(Exception):
    """Żądana ilość przekracza to, co dziś da się zarezerwować."""


@transaction.atomic
def reserve(
    variant: ProductVariant,
    quantity: int,
    ttl: timedelta = RESERVATION_TTL,
) -> Reservation | None:
    """Wyłącza ilość wariantu z dostępności na czas płatności.

    Produkt na zamówienie nie ma stanu, więc nie tworzy rezerwacji i zwraca
    `None` (ADR 0024) — nie jest to błąd, tylko brak czego rezerwować.

    Wiersz stanu jest blokowany na czas sprawdzenia: bez blokady dwa
    równoległe zamówienia na ostatnią sztukę odczytałyby tę samą dostępność
    i oba założyłyby rezerwację.
    """
    if quantity < 1:
        raise ValueError("quantity must be positive")
    if variant.product.is_made_to_order:
        return None

    item = InventoryItem.objects.select_for_update().filter(variant=variant).first()
    if item is None:
        raise InsufficientStock(
            f"{variant.sku} nie ma stanu magazynowego, więc nie ma czego rezerwować."
        )

    available = item.available
    if quantity > available:
        raise InsufficientStock(
            f"{variant.sku}: dostępne {available} szt., żądane {quantity}."
        )

    return Reservation.objects.create(
        variant=variant,
        quantity=quantity,
        expires_at=timezone.now() + ttl,
    )


@transaction.atomic
def release(reservation: Reservation) -> Reservation:
    """Zwalnia rezerwację; stan wraca do dostępności bez ruchu magazynowego.

    Zwolnienie nie zmienia stanu z ruchów, bo towar nigdy magazynu nie
    opuścił — zmienia się tylko to, ile z niego wolno sprzedać.
    """
    _reject_unless_active(reservation, "zwolnić")
    reservation.status = ReservationStatus.RELEASED
    reservation.save(update_fields=["status", "updated_at"])
    return reservation


@transaction.atomic
def consume(reservation: Reservation) -> StockMovement:
    """Rozlicza rezerwację ruchem magazynowym — towar schodzi ze stanu.

    Dopiero tutaj stan faktycznie maleje: do chwili zapłaty towar leży
    w magazynie, tylko wyłączony ze sprzedaży. Ruch jest tym samym bytem,
    co dostawa czy ubytek, więc historia dalej tłumaczy dzisiejszy stan.
    """
    _reject_unless_active(reservation, "rozliczyć")

    item = (
        InventoryItem.objects.select_for_update()
        .filter(variant_id=reservation.variant_id)  # type: ignore[missing-attribute]
        .first()
    )
    if item is None:
        raise InsufficientStock(
            "Rezerwacja wskazuje wariant bez stanu magazynowego — nie ma czego zdjąć."
        )

    movement = StockMovement.objects.create(
        item=item,
        quantity=-reservation.quantity,
        reason=StockMovementReason.SALE,
        note=f"Rezerwacja {reservation.pk}",
    )
    reservation.status = ReservationStatus.CONSUMED
    reservation.save(update_fields=["status", "updated_at"])
    return movement


def _reject_unless_active(reservation: Reservation, action: str) -> None:
    """Zwolnienie i rozliczenie dotyczą wyłącznie rezerwacji aktywnej.

    Przeterminowana rezerwacja jest tu jeszcze do zwolnienia — zadanie
    okresowe robi dokładnie to samo, tylko hurtowo.
    """
    if reservation.status != ReservationStatus.ACTIVE:
        raise ValueError(
            f"Rezerwacji ze statusem „{reservation.get_status_display()}” "  # type: ignore[missing-attribute]
            f"nie da się {action}."
        )
