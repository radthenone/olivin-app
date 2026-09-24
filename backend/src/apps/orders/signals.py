from __future__ import annotations

from allauth.account.signals import email_confirmed
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.notifications.models import NotificationKind
from apps.notifications.services import notify
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
    """Zapamiętuje poprzedni status — powiadomienia i premium go potrzebują.

    Zapytanie tylko przy istniejącym wierszu: nowo tworzone zamówienie nie
    ma poprzedniego statusu do porównania.
    """
    instance._previous_status = None  # type: ignore[attr-defined]
    if instance.pk:
        instance._previous_status = (  # type: ignore[attr-defined]
            Order.objects.filter(pk=instance.pk)
            .values_list("status", flat=True)
            .first()
        )


@receiver(post_save, sender=Order, dispatch_uid="orders_grant_premium_on_delivery")
def _grant_premium_on_delivery(sender, instance: Order, **kwargs) -> None:
    """Dostarczone zamówienie liczy się do progu premium (`CONTEXT.md`, Membership).

    Zamówienie gościa nie ma komu nadać premium — członkostwo mieszka na
    profilu konta. Nadanie czeka na `on_commit`: sygnał nie ma pewności, że
    wywołujący jest w transakcji, a licząc próg zaraz po `save()`, mógłby
    zobaczyć zamówienie, które i tak zostanie wycofane przez rollback.

    Sygnał wisi na `Model.save()`, więc `Order.objects.filter(...).update()`
    i `bulk_update()` go omijają — status zmieniony tą drogą nie nalicza
    premium. W tym kodzie jedyna droga do `delivered` to `save()`
    (`transition_to()` albo panel admina), więc to nie jest luka, dopóki
    nikt nie doda masowej zmiany statusu.
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

        transaction.on_commit(
            lambda: grant_premium_if_eligible(instance.user)  # type: ignore[bad-argument-type]
        )


@receiver(post_save, sender=Order, dispatch_uid="orders_notify_on_status_change")
def _notify_on_status_change(sender, instance: Order, created: bool, **kwargs) -> None:
    """Powiadamia o każdym przejściu statusu, w tym o `paid` (#156).

    Jedno miejsce dla wszystkich przejść: `transition_to()` jest jedyną drogą
    do zmiany statusu poza tworzeniem zamówienia, więc podpięcie tu pokrywa
    `mark_paid()` (webhook Stripe, zamówienie opłacone kuponem) i panel
    admina bez osobnych wywołań w każdym z nich.
    """
    if created:
        return
    previous_status = getattr(instance, "_previous_status", None)
    if previous_status is None or previous_status == instance.status:
        return

    kind = (
        NotificationKind.ORDER_PAID
        if instance.status == OrderStatus.PAID
        else NotificationKind.ORDER_STATUS_CHANGED
    )
    payload = {
        "order_number": instance.number,
        "status_label": instance.get_status_display(),  # type: ignore[missing-attribute]
    }
    # Gość nie ma konta, ale ma zawsze e-mail (`Order._resolve_email`) — dostaje
    # sam e-mail, bez rekordu w aplikacji (`notify()`).
    recipient = instance.user if instance.user_id is not None else instance.email  # type: ignore[missing-attribute]
    transaction.on_commit(lambda: notify(recipient, kind, payload))  # type: ignore[bad-argument-type]
