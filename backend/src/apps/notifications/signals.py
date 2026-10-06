"""Odbiorniki sygnałów powiadomień (#203)."""

from __future__ import annotations

from allauth.account.signals import email_confirmed
from django.dispatch import receiver

from apps.notifications.newsletter import transfer_to_account


@receiver(email_confirmed, dispatch_uid="notifications_move_newsletter_to_account")
def move_newsletter_subscription_to_account(
    sender, request, email_address, **kwargs
) -> None:
    """Konto przejmuje aktywną subskrypcję dopiero po potwierdzeniu adresu.

    Jak zamówienia gościa (`orders/signals.py`): samo założenie konta na
    cudzy adres nie jest dowodem właściciela, a niepotwierdzone konto jest
    potem sprzątane — subskrypcja przepadłaby razem z nim.
    """
    transfer_to_account(email_address.user, email=email_address.email)
