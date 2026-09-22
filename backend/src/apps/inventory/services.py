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


class ReservationError(Exception):
    """Wspólny rodzic odmów magazynu — jeden wyjątek do złapania w kasie."""


class InsufficientStock(ReservationError):
    """Żądana ilość przekracza to, co dziś da się zarezerwować."""


class ReservationNotActive(ReservationError):
    """Rezerwacja już nie trzyma stanu: zwolniona, rozliczona albo po terminie.

    Przy rozliczaniu to sytuacja do obsłużenia, a nie do zignorowania:
    zapłata doszła do skutku, ale towar wrócił w międzyczasie do sprzedaży
    i mógł zostać sprzedany komu innemu.
    """


@transaction.atomic
def reserve(
    variant: ProductVariant,
    quantity: int,
    ttl: timedelta = RESERVATION_TTL,
    order=None,
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

    # `order_by()` czyści domyślne `Meta.ordering = ["variant__sku"]`:
    # sortowanie po kolumnie ze złączenia kazałoby `FOR UPDATE` zablokować
    # także wiersz wariantu, czyli znacznie więcej, niż tu potrzeba.
    item = (
        InventoryItem.objects.select_for_update()
        .order_by()
        .filter(variant=variant)
        .first()
    )
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
        order=order,
        expires_at=timezone.now() + ttl,
    )


@transaction.atomic
def release(reservation: Reservation) -> Reservation:
    """Zwalnia rezerwację; stan wraca do dostępności bez ruchu magazynowego.

    Zwolnienie nie zmienia stanu z ruchów, bo towar nigdy magazynu nie
    opuścił — zmienia się tylko to, ile z niego wolno sprzedać.
    """
    _reject_unless_active(reservation, "zwolnić", allow_expired=True)
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
        .order_by()
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


@transaction.atomic
def restock(reservation: Reservation, note: str = "") -> StockMovement:
    """Przywraca na stan towar rozliczonej rezerwacji ruchem `return`.

    Rezerwacja zostaje `consumed` — sprzedaż się odbyła, a zwrot jest
    osobnym ruchem, żeby historia pokazała oba zdarzenia, a nie ich sumę.
    """
    if reservation.status != ReservationStatus.CONSUMED:
        raise ReservationNotActive(
            "Na stan wraca wyłącznie towar z rozliczonej rezerwacji."
        )
    item = InventoryItem.objects.get(variant_id=reservation.variant_id)  # type: ignore[missing-attribute]
    return StockMovement.objects.create(
        item=item,
        quantity=reservation.quantity,
        reason=StockMovementReason.RETURN,
        note=note or f"Rezerwacja {reservation.pk}",
    )


def _reject_unless_active(
    reservation: Reservation, action: str, *, allow_expired: bool = False
) -> None:
    """Sprawdza, czy rezerwacja jest jeszcze w stanie, w którym wolno ją ruszyć.

    Zwolnienie przepuszcza rezerwację po terminie — robi wtedy dokładnie to,
    co hurtem robi zadanie okresowe. Rozliczenie **nie**: po terminie stan
    wrócił już do sprzedaży i mógł zostać sprzedany komu innemu, więc
    zdjęcie go drugi raz zeszłoby poniżej zera.
    """
    if reservation.status != ReservationStatus.ACTIVE:
        raise ReservationNotActive(
            f"Rezerwacji ze statusem „{reservation.get_status_display()}” "  # type: ignore[missing-attribute]
            f"nie da się {action}."
        )
    if not allow_expired and not reservation.is_active:
        raise ReservationNotActive(
            f"Rezerwacja wygasła {reservation.expires_at:%Y-%m-%d %H:%M} — "
            f"stan wrócił do sprzedaży, więc nie da się jej {action}."
        )
