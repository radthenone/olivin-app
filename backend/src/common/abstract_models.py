import uuid

from django.db import models


class TimestampedModel(models.Model):
    """Abstract base model that provides timestamp fields."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the record was created",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the record was last updated",
    )

    class Meta:
        abstract = True
        # Identyfikator jako rozstrzygnięcie remisu: sam `created_at` nie jest
        # unikalny, a przy paginacji dwa rekordy z tą samą chwilą utworzenia
        # potrafią powtórzyć się na jednej stronie i zniknąć z następnej.
        ordering = ["-created_at", "-id"]
