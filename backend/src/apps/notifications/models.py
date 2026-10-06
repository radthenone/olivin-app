from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from django.db import models
from django.utils import timezone

from common import TimestampedModel

if TYPE_CHECKING:
    from apps.accounts.models import Customer


class NotificationKind(models.TextChoices):
    """Rodzaj powiadomienia (`CONTEXT.md`, Notification)."""

    ORDER_STATUS_CHANGED = "order_status_changed", "Zmiana statusu zamówienia"
    ORDER_PAID = "order_paid", "Zamówienie opłacone"
    DOCUMENT_READY = "document_ready", "Dokument gotowy"
    RETURN_REQUEST_STATUS_CHANGED = (
        "return_request_status_changed",
        "Zmiana stanu zgłoszenia zwrotu",
    )
    RETURN_SETTLED = "return_settled", "Rozliczenie zwrotu"
    WATCH_RESTOCK = "watch_restock", "Wariant wrócił na stan"
    WATCH_PRICE_DROP = "watch_price_drop", "Spadek ceny wariantu"


# Transakcyjne docierają zawsze; rodzaje spoza tego zbioru są marketingowe
# i respektują `NotificationPreference` (`CONTEXT.md`, Notification).
TRANSACTIONAL_KINDS: frozenset[str] = frozenset(
    {
        NotificationKind.ORDER_STATUS_CHANGED,
        NotificationKind.ORDER_PAID,
        NotificationKind.DOCUMENT_READY,
        NotificationKind.RETURN_REQUEST_STATUS_CHANGED,
        NotificationKind.RETURN_SETTLED,
    }
)


class NotificationQuerySet(models.QuerySet["Notification"]):
    def unread(self) -> NotificationQuerySet:
        return self.filter(is_read=False)


class Notification(TimestampedModel):
    """Zdarzenie zapisane dla klienta (`CONTEXT.md`, Notification).

    Tylko dla konta: gość nie ma gdzie zobaczyć historii powiadomień w
    aplikacji, więc dostaje wyłącznie e-mail (`notify()`).
    """

    user = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text="Klient, do którego należy powiadomienie",
    )
    kind = models.CharField(
        max_length=32,
        choices=NotificationKind.choices,
        help_text="Rodzaj zdarzenia",
    )
    message = models.TextField(help_text="Treść powiadomienia do wyświetlenia")
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Dane zdarzenia, np. numer zamówienia",
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    objects: NotificationQuerySet = NotificationQuerySet.as_manager()  # type: ignore[bad-assignment]

    class Meta:
        verbose_name = "Powiadomienie"
        verbose_name_plural = "Powiadomienia"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.get_kind_display()} — {self.user}"  # type: ignore[missing-attribute]

    def mark_read(self) -> None:
        if self.is_read:
            return
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=["is_read", "read_at", "updated_at"])


class NotificationPreference(TimestampedModel):
    """Zgoda klienta na komunikaty marketingowe, osobno per kanał (`CONTEXT.md`).

    Nie obejmuje komunikatów transakcyjnych — te docierają zawsze, bez
    względu na te ustawienia (`TRANSACTIONAL_KINDS`).
    """

    user = models.OneToOneField(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        related_name="notification_preference",
    )
    marketing_email = models.BooleanField(
        default=False, help_text="Zgoda na marketing e-mailem"
    )
    marketing_push = models.BooleanField(
        default=False, help_text="Zgoda na marketing push"
    )

    class Meta:
        verbose_name = "Preferencja powiadomień"
        verbose_name_plural = "Preferencje powiadomień"

    def __str__(self) -> str:
        return f"Preferencje {self.user}"

    @classmethod
    def for_user(cls, user: Customer) -> NotificationPreference:
        """Preferencje klienta; domyślne (bez zgody) przy pierwszym odczycie."""
        preference, _ = cls.objects.get_or_create(user=user)
        return preference


class PushPlatform(models.TextChoices):
    """Platforma urządzenia push — do statystyk i strojenia treści."""

    IOS = "ios", "iOS"
    ANDROID = "android", "Android"


class PushDevice(TimestampedModel):
    """Urządzenie klienta zarejestrowane do powiadomień push (`CONTEXT.md`).

    Jedno konto może mieć wiele urządzeń; token Expo jest globalnie
    unikalny — jedno urządzenie należy do jednego konta. Rejestracja jest
    idempotentna: powtórzenie z tym samym tokenem odświeża właściciela
    i czas użycia. `CASCADE` przy koncie realizuje anonimizację
    (`CONTEXT.md`, Account anonymisation): skasowanie konta kasuje urządzenia.
    """

    user = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        related_name="push_devices",
        help_text="Klient, do którego należy urządzenie",
    )
    token = models.CharField(
        max_length=255,
        unique=True,
        help_text="Token push Expo (ExponentPushToken[...])",
    )
    platform = models.CharField(
        max_length=16,
        choices=PushPlatform.choices,
        help_text="Platforma urządzenia",
    )
    last_used_at = models.DateTimeField(
        default=timezone.now,
        help_text="Ostatnia rejestracja lub wysyłka na to urządzenie",
    )

    class Meta:
        verbose_name = "Urządzenie push"
        verbose_name_plural = "Urządzenia push"
        ordering = ["-last_used_at", "-id"]

    def __str__(self) -> str:
        return f"{self.platform} — {self.user}"  # type: ignore[missing-attribute]


class NewsletterStatus(models.TextChoices):
    """Stan subskrypcji newslettera (`CONTEXT.md`, NewsletterSubscription)."""

    PENDING = "pending", "Niepotwierdzona"
    ACTIVE = "active", "Aktywna"
    UNSUBSCRIBED = "unsubscribed", "Wypisana"


class NewsletterSubscription(TimestampedModel):
    """Zapis na newsletter bez konta, aktywny po potwierdzeniu linkiem (#203).

    Adres jest przechowywany małymi literami, więc unikalność pola wystarcza
    do deduplikacji. Token potwierdzenia jest odnawiany przy ponownym
    zapisie po wypisie; token wypisu jest stały — każdy wysłany link działa.
    Po założeniu konta na ten adres subskrypcja przechodzi w
    `NotificationPreference.marketing_email` i znika (`newsletter.py`).
    """

    email = models.EmailField(unique=True, help_text="Adres zapisany małymi literami")
    status = models.CharField(
        max_length=16,
        choices=NewsletterStatus.choices,
        default=NewsletterStatus.PENDING,
        help_text="Niepotwierdzona do kliknięcia linku, potem aktywna albo wypisana",
    )
    confirmation_token = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False
    )
    unsubscribe_token = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False
    )
    confirmed_at = models.DateTimeField(
        null=True, blank=True, help_text="Chwila potwierdzenia linkiem"
    )

    class Meta:
        verbose_name = "Subskrypcja newslettera"
        verbose_name_plural = "Subskrypcje newslettera"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.email} ({self.status})"
