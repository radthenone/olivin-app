# Generated for issue #201 — Watch a variant for restock or price drop.

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models

import common.money


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("products", "0008_product_claim_flags"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Watch",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when the record was created",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when the record was last updated",
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("restock", "Powrót na stan"),
                            ("price_drop", "Spadek ceny"),
                        ],
                        help_text="Rodzaj wyzwalacza",
                        max_length=16,
                    ),
                ),
                (
                    "price_at_watch",
                    common.money.MoneyAmountField(
                        blank=True,
                        help_text="Cena w chwili zapisu (grosze) — tylko dla spadku ceny",
                        null=True,
                    ),
                ),
                (
                    "currency",
                    common.money.CurrencyField(
                        default="PLN",
                        help_text="Kod waluty ISO 4217",
                        max_length=3,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Aktywna"), ("sent", "Wysłana")],
                        default="active",
                        help_text="Aktywna czeka; wysłana wygasła",
                        max_length=16,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        help_text="Klient obserwujący wariant",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="watches",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "variant",
                    models.ForeignKey(
                        help_text="Obserwowany wariant",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="watches",
                        to="products.productvariant",
                    ),
                ),
            ],
            options={
                "verbose_name": "Obserwowany wariant",
                "verbose_name_plural": "Obserwowane warianty",
                "ordering": ["-created_at", "-id"],
                "constraints": [
                    models.UniqueConstraint(
                        condition=models.Q(status="active"),
                        fields=("user", "variant", "kind"),
                        name="watch_one_active_per_user_variant_kind",
                    ),
                    models.CheckConstraint(
                        condition=(
                            models.Q(kind="price_drop", price_at_watch__isnull=False)
                            | models.Q(kind="restock", price_at_watch__isnull=True)
                        ),
                        name="watch_price_only_for_price_drop",
                    ),
                ],
            },
        ),
    ]
