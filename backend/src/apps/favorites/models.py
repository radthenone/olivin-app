from __future__ import annotations

from django.conf import settings
from django.db import models

from common import TimestampedModel


class Favorite(TimestampedModel):
    """Produkt zapisany przez klienta jako lubiany (`CONTEXT.md`, Favorite).

    Lista jest wspólna dla wszystkich urządzeń klienta i bez limitu. Dotyczy
    produktu, nie wariantu — para użytkownik+produkt jest unikalna, więc
    dodanie już ulubionego produktu jest bezpiecznym powtórzeniem, nie
    błędem. Rekord przeżywa cofnięcie publikacji produktu — znika tylko
    z list w API, żeby po powrocie produktu na sklep serduszko nie musiało
    być zaznaczane od nowa.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="favorited_by",
    )

    class Meta:
        verbose_name = "Ulubiony produkt"
        verbose_name_plural = "Ulubione produkty"
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                name="favorite_one_per_user_per_product",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user} — {self.product}"
