"""Newsletter: double opt-in, wypis bez logowania, przejście na konto (#203).

`CONTEXT.md`, NewsletterSubscription. Wypis działa bez logowania na dwa
sposoby: subskrypcja ma własny `unsubscribe_token`, a konto dostaje w
mailu podpisany token adresu (`account_unsubscribe_token`) — bez nowej
tabeli i bez ujawniania identyfikatora konta.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from django.conf import settings
from django.core import signing
from django.db import transaction
from django.utils import timezone

from apps.consents.models import Consent, ConsentDocument, ConsentKind
from apps.notifications.models import (
    NewsletterStatus,
    NewsletterSubscription,
    NotificationPreference,
)
from core.integrations.notifications.mail import send_notification_email

if TYPE_CHECKING:
    from apps.accounts.models import CustomUser

_UNSUBSCRIBE_SALT = "newsletter-unsubscribe"


class NoMarketingDocumentError(Exception):
    """Brak bieżącej wersji zgody marketingowej — zapisu nie da się udokumentować."""


def _normalise(email: str) -> str:
    return email.strip().lower()


def _parse_uuid(token: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(token))
    except ValueError:
        return None


def confirm_url(subscription: NewsletterSubscription) -> str:
    return settings.NEWSLETTER_CONFIRM_URL.format(
        token=subscription.confirmation_token
    )


def subscription_unsubscribe_url(subscription: NewsletterSubscription) -> str:
    return settings.NEWSLETTER_UNSUBSCRIBE_URL.format(
        token=subscription.unsubscribe_token
    )


def account_unsubscribe_token(email: str) -> str:
    """Podpisany token adresu konta — wypis z maila bez logowania."""
    return signing.dumps(_normalise(email), salt=_UNSUBSCRIBE_SALT)


def account_unsubscribe_url(email: str) -> str:
    return settings.NEWSLETTER_UNSUBSCRIBE_URL.format(
        token=account_unsubscribe_token(email)
    )


def _send_confirmation(subscription: NewsletterSubscription) -> None:
    link = confirm_url(subscription)
    transaction.on_commit(
        lambda: send_notification_email(
            to=subscription.email,
            subject="Potwierdź zapis na newsletter",
            body=(
                "Dziękujemy za zapis na newsletter. Potwierdź adres, "
                f"klikając w link: {link}\n\n"
                "Jeśli to nie Ty, zignoruj tę wiadomość — bez potwierdzenia "
                "nic do Ciebie nie wyślemy."
            ),
        ),
        robust=True,
    )


@transaction.atomic
def subscribe(email: str) -> None:
    """Zapis na newsletter; aktywny dopiero po kliknięciu linku z maila.

    Nie zwraca niczego, co różniłoby nowy adres od istniejącego — wywołujący
    (API) odpowiada zawsze tak samo. Aktywna subskrypcja nie dostaje maila;
    niepotwierdzona — ponowny link; nowa albo wypisana — nową zgodę gościa
    na bieżącą wersję zgody marketingowej i świeży token potwierdzenia.
    """
    document = ConsentDocument.objects.current(ConsentKind.MARKETING)
    if document is None:
        raise NoMarketingDocumentError
    address = _normalise(email)
    subscription, created = (
        NewsletterSubscription.objects.select_for_update().get_or_create(
            email=address
        )
    )
    if subscription.status == NewsletterStatus.ACTIVE:
        return
    if created or subscription.status == NewsletterStatus.UNSUBSCRIBED:
        if not created:
            subscription.status = NewsletterStatus.PENDING
            subscription.confirmation_token = uuid.uuid4()
            subscription.confirmed_at = None
            subscription.save(
                update_fields=[
                    "status",
                    "confirmation_token",
                    "confirmed_at",
                    "updated_at",
                ]
            )
        Consent.objects.create(email=address, document=document)
    _send_confirmation(subscription)


@transaction.atomic
def confirm(token: str) -> bool:
    """Potwierdza niepotwierdzoną subskrypcję; `False` dla nieznanego linku.

    Gdy adres jest już potwierdzonym adresem konta, subskrypcja od razu
    przechodzi w jego preferencje (`transfer_to_account`).
    """
    parsed = _parse_uuid(token)
    if parsed is None:
        return False
    subscription = (
        NewsletterSubscription.objects.select_for_update()
        .filter(confirmation_token=parsed, status=NewsletterStatus.PENDING)
        .first()
    )
    if subscription is None:
        return False
    subscription.status = NewsletterStatus.ACTIVE
    subscription.confirmed_at = timezone.now()
    subscription.save(update_fields=["status", "confirmed_at", "updated_at"])

    from allauth.account.models import EmailAddress

    verified = (
        EmailAddress.objects.filter(email__iexact=subscription.email, verified=True)
        .select_related("user")
        .first()
    )
    if verified is not None:
        transfer_to_account(verified.user, email=subscription.email)
    return True


@transaction.atomic
def unsubscribe(token: str) -> bool:
    """Wypis bez logowania; `False` dla nieznanego albo sfałszowanego tokenu.

    Token subskrypcji wypisuje ją; podpisany token konta wyłącza
    `marketing_email` konta i wypisuje subskrypcję na ten sam adres.
    """
    parsed = _parse_uuid(token)
    if parsed is not None:
        return bool(
            NewsletterSubscription.objects.filter(unsubscribe_token=parsed).update(
                status=NewsletterStatus.UNSUBSCRIBED, updated_at=timezone.now()
            )
        )
    try:
        address = signing.loads(token, salt=_UNSUBSCRIBE_SALT)
    except signing.BadSignature:
        return False
    NotificationPreference.objects.filter(user__email__iexact=address).update(
        marketing_email=False, updated_at=timezone.now()
    )
    NewsletterSubscription.objects.filter(email=address).update(
        status=NewsletterStatus.UNSUBSCRIBED, updated_at=timezone.now()
    )
    return True


def transfer_to_account(user: CustomUser, *, email: str) -> None:
    """Przenosi aktywną subskrypcję potwierdzonego adresu konta do `marketing_email`.

    Subskrypcja znika — od teraz zgodę trzyma preferencja konta. Zgoda gościa
    (`Consent`) zostaje jako historia. Niepotwierdzona subskrypcja czeka na
    kliknięcie linku (`confirm` przeniesie ją wtedy sama).
    """
    deleted, _ = NewsletterSubscription.objects.filter(
        email=_normalise(email), status=NewsletterStatus.ACTIVE
    ).delete()
    if deleted:
        preference = NotificationPreference.for_user(user)
        preference.marketing_email = True
        preference.save(update_fields=["marketing_email", "updated_at"])
