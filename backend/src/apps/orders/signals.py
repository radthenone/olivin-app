from __future__ import annotations

from allauth.account.signals import email_confirmed
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.orders.models import Order, OrderStatus
from apps.orders.services.order import attach_guest_orders


@receiver(email_confirmed, dispatch_uid="orders_attach_guest_orders")
def attach_guest_orders_on_email_confirmed(
    sender, request, email_address, **kwargs
) -> None:
    """Zamówienia gościa trafiają do konta dopiero po potwierdzeniu adresu.

    Nie przy zakładaniu konta: samo wpisanie cudzego adresu w rejestracji
    otworzyłoby obcej osobie historię zakupów wraz z adresem dostawy.
    Potwierdzenie jest dowodem, że to ten sam człowiek — a weryfikacja jest
    w tym sklepie obowiązkowa (`ACCOUNT_EMAIL_VERIFICATION = "mandatory"`).

    Sygnał, a nie krok w rejestracji: adres potwierdza się też po zmianie
    e-maila i po dodaniu drugiego adresu do konta.
    """
    attach_guest_orders(email_address.user, email=email_address.email)


@receiver(pre_save, sender=Order, dispatch_uid="orders_capture_previous_status")
def _capture_previous_status(sender, instance: Order, **kwargs) -> None:
    """Zapamiętuje poprzedni status, żeby wykryć wejście w `delivered`.

    Zapytanie tylko wtedy, gdy zapis wprowadza `delivered` — to jedyne
    przejście, które coś uruchamia; reszta zapisów nie płaci za sprawdzenie.
    """
    instance._previous_status = None  # type: ignore[attr-defined]
    if instance.pk and instance.status == OrderStatus.DELIVERED:
        instance._previous_status = (  # type: ignore[attr-defined]
            Order.objects.filter(pk=instance.pk)
            .values_list("status", flat=True)
            .first()
        )


@receiver(post_save, sender=Order, dispatch_uid="orders_grant_premium_on_delivery")
def _grant_premium_on_delivery(sender, instance: Order, **kwargs) -> None:
    """Dostarczone zamówienie liczy się do progu premium (`CONTEXT.md`, Membership).

    Zamówienie gościa nie ma komu nadać premium — członkostwo mieszka na
    profilu konta.
    """
    previous_status = getattr(instance, "_previous_status", None)
    if (
        instance.status == OrderStatus.DELIVERED
        and previous_status != OrderStatus.DELIVERED
        and instance.user_id is not None  # type: ignore[missing-attribute]
    ):
        from apps.accounts.services.membership_service import (
            grant_premium_if_eligible,
        )

        grant_premium_if_eligible(instance.user)  # type: ignore[bad-argument-type]
