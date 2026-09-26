from __future__ import annotations

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from common import TimestampedModel

COMMENT_MAX_LENGTH = 1000


class ReviewStatus(models.TextChoices):
    """Stan moderacji opinii (`CONTEXT.md`, Review)."""

    PENDING = "pending", "Oczekuje na moderację"
    APPROVED = "approved", "Opublikowana"
    REJECTED = "rejected", "Odrzucona"


class ReviewQuerySet(models.QuerySet["Review"]):
    def approved(self) -> ReviewQuerySet:
        return self.filter(status=ReviewStatus.APPROVED)


class Review(TimestampedModel):
    """Opinia klienta o kupionym produkcie (`CONTEXT.md`, Review).

    Jedna opinia na klienta na produkt — kolejna próba jest edycją, nie
    nowym wierszem. Publicznie widoczna dopiero po akceptacji sklepu;
    edycja treści zawsze cofa status do moderacji, bo sklep zaakceptował
    poprzednią wersję, nie tę, która właśnie powstała.
    """

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Ocena w skali 1-5",
    )
    comment = models.CharField(
        max_length=COMMENT_MAX_LENGTH,
        blank=True,
        help_text="Krótki komentarz, opcjonalny",
    )
    status = models.CharField(
        max_length=16,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
        help_text="Publicznie widoczna wyłącznie w stanie approved",
    )

    objects: ReviewQuerySet = ReviewQuerySet.as_manager()  # type: ignore[bad-assignment]

    class Meta:
        verbose_name = "Opinia"
        verbose_name_plural = "Opinie"
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "user"],
                name="review_one_per_customer_per_product",
            ),
            models.CheckConstraint(
                condition=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name="review_rating_in_range",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product} — {self.user} ({self.rating})"

    def restart_moderation(self) -> None:
        """Edycja treści zawsze wraca opinię do moderacji."""
        self.status = ReviewStatus.PENDING
