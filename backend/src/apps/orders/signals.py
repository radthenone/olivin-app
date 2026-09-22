from __future__ import annotations

from allauth.account.signals import email_confirmed
from django.dispatch import receiver

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
