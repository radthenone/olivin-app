from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from apps.products.models.metal_rate import MetalRate, MetalRateStatus
from common.money import Money


@dataclass(frozen=True, slots=True)
class ActivationResult:
    rate: MetalRate
    previous: Money | None
    previous_rate_id: object | None


def activate_rate(rate: MetalRate, activated_by=None) -> ActivationResult:
    """Zatwierdza kurs: archiwizuje poprzedni, kolejkuje przeliczenie i e-mail.

    Trzy rzeczy muszą się zdarzyć razem albo wcale — archiwizacja poprzedniego
    kursu, aktywacja nowego i przeliczenie cen. Dwa aktywne kursy tego samego
    kruszcu oznaczałyby cenę zależną od kolejności wierszy w bazie, a katalog
    przeliczony wobec kursu, który nie wszedł, byłby gorszy od nieprzeliczonego.

    Zadanie w tle i wiadomość idą dopiero po zatwierdzeniu transakcji: inaczej
    worker mógłby zacząć liczyć wobec stanu, który za chwilę zostanie wycofany.
    """
    from apps.products.tasks import (
        notify_owner_about_rate_activation,
        recalculate_variant_prices,
    )

    with transaction.atomic():
        previous = (
            MetalRate.objects.select_for_update()
            .active()
            .filter(metal=rate.metal, fineness=rate.fineness)
            .exclude(pk=rate.pk)
            .first()
        )
        previous_price = previous.price if previous else None
        previous_id = previous.pk if previous else None

        if previous is not None:
            previous.status = MetalRateStatus.ARCHIVED
            previous.save(update_fields=["status", "updated_at"])

        rate.status = MetalRateStatus.ACTIVE
        rate.activated_at = timezone.now()
        rate.activated_by = activated_by
        rate.save(
            update_fields=["status", "activated_at", "activated_by", "updated_at"]
        )

    # `shared_task` zwraca w stubach zwykłą funkcję, bez `delay`.
    transaction.on_commit(
        lambda: recalculate_variant_prices.delay(  # type: ignore[missing-attribute]
            rate.metal, rate.fineness
        )
    )
    transaction.on_commit(
        lambda: notify_owner_about_rate_activation.delay(  # type: ignore[missing-attribute]
            str(rate.pk),
            str(previous_id) if previous_id else None,
        )
    )

    return ActivationResult(
        rate=rate, previous=previous_price, previous_rate_id=previous_id
    )
