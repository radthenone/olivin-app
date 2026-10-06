# Rodzaje marketingowe Watch (issue #201) — zmiana stanu, bez zmiany schematu.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0003_notification_kind_return_settled"),
    ]

    operations = [
        migrations.AlterField(
            model_name="notification",
            name="kind",
            field=models.CharField(
                choices=[
                    ("order_status_changed", "Zmiana statusu zamówienia"),
                    ("order_paid", "Zamówienie opłacone"),
                    ("document_ready", "Dokument gotowy"),
                    ("return_request_status_changed", "Zmiana stanu zgłoszenia zwrotu"),
                    ("return_settled", "Rozliczenie zwrotu"),
                    ("watch_restock", "Wariant wrócił na stan"),
                    ("watch_price_drop", "Spadek ceny wariantu"),
                ],
                help_text="Rodzaj zdarzenia",
                max_length=32,
            ),
        ),
    ]
