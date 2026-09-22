from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone

from common import TimestampedModel


class ConsentKind(models.TextChoices):
    TERMS = "terms", "Regulamin"
    PRIVACY = "privacy", "Polityka prywatności"
    MARKETING = "marketing", "Komunikacja marketingowa"


class ConsentDocumentQuerySet(models.QuerySet["ConsentDocument"]):
    def effective(self) -> ConsentDocumentQuerySet:
        """Wersje, które już obowiązują — przyszła wersja jeszcze nie jest bieżąca."""
        return self.filter(effective_from__lte=timezone.localdate())

    def current(self, kind: str) -> ConsentDocument | None:
        """Bieżąca wersja dokumentu danego rodzaju; `None`, gdy żadnej nie ma."""
        return self.effective().filter(kind=kind).order_by("-effective_from").first()

    def current_for_all_kinds(self) -> list[ConsentDocument]:
        """Po jednej bieżącej wersji na rodzaj, w kolejności rodzajów."""
        documents = [self.current(kind) for kind in ConsentKind.values]
        return [document for document in documents if document is not None]


class ConsentDocument(TimestampedModel):
    """Wersja regulaminu, polityki prywatności albo zgody marketingowej.

    Wersjonowanie jest tu istotą, nie dodatkiem (`CONTEXT.md`, Consent):
    zgoda odnosi się do konkretnej wersji, a nowa wersja wymaga ponownej
    akceptacji. Dokument nie ma treści — ta żyje na stronie sklepu; model
    trzyma tylko to, co potrzebne, żeby rozstrzygnąć, czy zgoda jest aktualna.
    """

    kind = models.CharField(
        max_length=16,
        choices=ConsentKind.choices,
        help_text="Rodzaj dokumentu",
    )
    version = models.CharField(
        max_length=32,
        help_text="Oznaczenie wersji, np. 2026-09; unikalne w obrębie rodzaju",
    )
    effective_from = models.DateField(
        help_text=(
            "Dzień, od którego wersja obowiązuje. Najnowsza obowiązująca "
            "wersja jest bieżącą; wcześniejsze zgody przestają być aktualne."
        ),
    )

    objects: ConsentDocumentQuerySet = ConsentDocumentQuerySet.as_manager()  # type: ignore[bad-assignment]

    class Meta:
        verbose_name = "Dokument zgody"
        verbose_name_plural = "Dokumenty zgód"
        ordering = ["kind", "-effective_from", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "version"],
                name="consent_document_version_unique_per_kind",
            )
        ]

    def __str__(self) -> str:
        return f"{self.get_kind_display()} {self.version}"  # type: ignore[missing-attribute]


class ConsentQuerySet(models.QuerySet["Consent"]):
    def for_subject(self, *, user=None, email: str | None = None) -> ConsentQuerySet:
        """Zgody użytkownika albo gościa po e-mailu — nigdy obu naraz.

        Zgoda gościa nie przechodzi na konto założone później na ten sam
        adres: konto akceptuje dokumenty samo, przy rejestracji.
        """
        if user is not None:
            return self.filter(user=user)
        if email:
            return self.filter(email__iexact=email)
        return self.none()

    def has_current_consent(
        self, kind: str, *, user=None, email: str | None = None
    ) -> bool:
        """Czy podmiot zaakceptował bieżącą wersję dokumentu danego rodzaju."""
        current = ConsentDocument.objects.current(kind)
        if current is None:
            return False
        return (
            self.for_subject(user=user, email=email).filter(document=current).exists()
        )


class Consent(TimestampedModel):
    """Zgoda klienta albo gościa na konkretną wersję dokumentu (`CONTEXT.md`, Consent).

    Podmiotem jest użytkownik albo e-mail gościa — dokładnie jedno. Wersja
    jest skopiowana z dokumentu w chwili udzielenia, żeby zapis pozostał
    czytelny, nawet gdyby dokument został kiedyś przenumerowany.
    """

    user = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="consents",
        help_text="Zalogowany klient, który udzielił zgody",
    )
    email = models.EmailField(
        blank=True,
        help_text="E-mail gościa bez konta; pusty przy zgodzie zalogowanego",
    )
    document = models.ForeignKey(
        ConsentDocument,
        on_delete=models.PROTECT,
        related_name="consents",
        help_text="Wersja dokumentu, której dotyczy zgoda",
    )
    version = models.CharField(
        max_length=32,
        editable=False,
        help_text="Kopia wersji dokumentu z chwili udzielenia zgody",
    )
    granted_at = models.DateTimeField(
        default=timezone.now,
        help_text="Chwila udzielenia zgody",
    )

    objects: ConsentQuerySet = ConsentQuerySet.as_manager()  # type: ignore[bad-assignment]

    class Meta:
        verbose_name = "Zgoda"
        verbose_name_plural = "Zgody"
        ordering = ["-granted_at", "-id"]
        indexes = [models.Index(Lower("email"), name="consent_email_lower_idx")]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(user__isnull=False, email="")
                    | models.Q(user__isnull=True) & ~models.Q(email="")
                ),
                name="consent_subject_is_user_xor_email",
            )
        ]

    def __str__(self) -> str:
        subject = self.email if self.user_id is None else str(self.user)  # type: ignore[missing-attribute]
        return f"{subject}: {self.document}"

    @property
    def kind(self) -> str:
        return self.document.kind

    def clean(self) -> None:
        super().clean()
        self._reject_ambiguous_subject()

    def save(self, *args, **kwargs) -> None:
        self._reject_ambiguous_subject()
        if not self.version:
            self.version = self.document.version
        super().save(*args, **kwargs)

    def _reject_ambiguous_subject(self) -> None:
        # Stuby nie generują kolumny `<fk>_id` — patrz `Product._reject_non_leaf_category`.
        has_user = self.user_id is not None  # type: ignore[missing-attribute]
        has_email = bool(self.email)
        if has_user and has_email:
            raise ValidationError(
                {"email": "Zgoda zalogowanego klienta nie ma osobnego e-maila."}
            )
        if not has_user and not has_email:
            raise ValidationError(
                {"email": "Zgoda gościa wymaga e-maila, zgoda klienta — konta."}
            )
