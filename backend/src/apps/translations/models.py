from __future__ import annotations

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from common import TimestampedModel


class Language(models.TextChoices):
    """Języki treści katalogu.

    Polski jest źródłem — nie ma dla niego wpisów w tej tabeli, bo tekst
    źródłowy siedzi na modelu. Lista jest wyliczeniem, żeby dołożenie
    kolejnego języka było jedną pozycją, a nie zmianą schematu.
    """

    EN = "en", "angielski"


SOURCE_LANGUAGE = "pl"


class TranslationSource(models.TextChoices):
    AUTO = "auto", "Automatyczne"
    MANUAL = "manual", "Poprawione ręcznie"


class TranslationQuerySet(models.QuerySet["Translation"]):
    def manual(self) -> TranslationQuerySet:
        return self.filter(source=TranslationSource.MANUAL)

    def for_object(self, obj) -> TranslationQuerySet:
        return self.filter(
            content_type=ContentType.objects.get_for_model(obj), object_id=obj.pk
        )


class Translation(TimestampedModel):
    """Tłumaczenie jednego pola tekstowego katalogu (`CONTEXT.md`, Translation).

    Osobna tabela, a nie kolumna na modelu: pól do przetłumaczenia jest
    kilka, języków przybędzie, a brak tłumaczenia ma być stanem widocznym —
    pusta kolumna nie odróżnia „jeszcze nieprzetłumaczone" od „przetłumaczone
    na pusty tekst".

    Tłumaczenie poprawione ręcznie nie jest nigdy nadpisywane przez automat:
    właściciel poprawia je, bo automat się pomylił.
    """

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    target = GenericForeignKey("content_type", "object_id")

    field = models.CharField(
        max_length=64,
        help_text="Nazwa pola modelu, którego dotyczy tłumaczenie",
    )
    language = models.CharField(
        max_length=8,
        choices=Language.choices,
        default=Language.EN,
        help_text="Język docelowy; polski jest źródłem i nie ma tu wpisów",
    )
    text = models.TextField(help_text="Przetłumaczony tekst")
    source = models.CharField(
        max_length=8,
        choices=TranslationSource.choices,
        default=TranslationSource.AUTO,
        help_text="Automat czy poprawka właściciela",
    )
    translated_at = models.DateTimeField(
        default=timezone.now,
        help_text="Kiedy powstało to brzmienie",
    )

    objects: TranslationQuerySet = TranslationQuerySet.as_manager()  # type: ignore[bad-assignment]

    class Meta:
        verbose_name = "Tłumaczenie"
        verbose_name_plural = "Tłumaczenia"
        ordering = ["content_type", "object_id", "field", "language"]
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id", "field", "language"],
                name="translation_one_per_field_and_language",
            )
        ]
        indexes = [models.Index(fields=["content_type", "object_id", "language"])]

    def __str__(self) -> str:
        return f"{self.field} [{self.language}]"

    @property
    def is_manual(self) -> bool:
        return self.source == TranslationSource.MANUAL
