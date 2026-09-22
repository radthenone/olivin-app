from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import CustomUser
from apps.orders.services.order import attach_guest_orders


@receiver(post_save, sender=CustomUser, dispatch_uid="orders_attach_guest_orders")
def attach_guest_orders_to_new_account(sender, instance, created, **kwargs) -> None:
    """Zamówienia gościa trafiają do konta założonego później na ten sam e-mail.

    Sygnał, a nie krok w rejestracji: konto powstaje też przez logowanie
    społecznościowe i przez panel, a klient w każdym z tych przypadków ma
    zastać swoją historię zakupów.
    """
    if created:
        attach_guest_orders(instance)
