from __future__ import annotations

import logging
from typing import Any, cast

from celery import shared_task
from django.utils import timezone

from core.integrations.push.base import ORDERS_CHANNEL, PushProviderTransientError

logger = logging.getLogger(__name__)

# Expo zaleca sprawdzać receipty ~15 minut po wysyłce (czyści je po 24 h).
RECEIPT_CHECK_DELAY_SECONDS = 15 * 60

# Ponawianie z rosnącym odstępem (z losowym rozrzutem) przy 429, 5xx i błędzie
# sieci — błąd żądania (4xx) nie jest ponawiany (ADR 0037).
_RETRY_OPTIONS: dict[str, Any] = {
    "autoretry_for": (PushProviderTransientError,),
    # 30, 60, 120, 240, 480 s — 429 od Expo potrzebuje oddechu, nie sekund.
    "retry_backoff": 30,
    "retry_backoff_max": 600,
    "retry_jitter": True,
    "max_retries": 5,
}


@shared_task(bind=True, **_RETRY_OPTIONS)
def send_push_notification(
    self,
    *,
    user_id: str,
    title: str,
    body: str,
    data: dict[str, Any] | None = None,
    # Domyślnie `orders`: zadania z kolejki sprzed #315 to w większości
    # transakcyjne — lepiej marketing z wysokim priorytetem niż zgubiony status.
    channel: str = ORDERS_CHANNEL,
) -> int:
    """Wysyła push na urządzenia klienta przez adapter (issue #202, #315).

    Asynchronicznie: `notify()` kolejkuje to zadanie po commicie, a błąd
    pusha nie blokuje e-maila ani rekordu w aplikacji. Błąd przejściowy
    (429, 5xx, sieć) jest ponawiany z rosnącym odstępem; pozostałe błędy
    dostawcy kończą zadanie cicho. Tokeny odrzucone przez Expo
    (`DeviceNotRegistered`) są kasowane, a tickety przyjętych wiadomości
    trafiają do `check_push_receipts` z opóźnieniem.
    """
    from apps.notifications.models import PushDevice
    from core.integrations.push.base import PushProviderError
    from core.integrations.push.registry import get_provider

    payload = data or {}
    tokens = list(
        PushDevice.objects.filter(user_id=user_id).values_list("token", flat=True)
    )
    if not tokens:
        return 0
    try:
        result = get_provider().send_push(
            tokens=tokens, title=title, body=body, data=payload, channel=channel
        )
    except PushProviderTransientError:
        raise
    except PushProviderError:
        logger.exception("Nie udało się wysłać pusha do klienta %s", user_id)
        return 0
    except Exception:
        logger.exception("Nieoczekiwany błąd wysyłki pusha do klienta %s", user_id)
        return 0
    invalid = result.invalid_tokens
    if invalid:
        PushDevice.objects.filter(user_id=user_id, token__in=invalid).delete()
    else:
        PushDevice.objects.filter(user_id=user_id, token__in=tokens).update(
            last_used_at=timezone.now()
        )
    if result.tickets:
        # `cast(Any, ...)`: pyrefly nie widzi `.apply_async` zadania Celery.
        cast(Any, check_push_receipts).apply_async(
            kwargs={"tickets": result.tickets},
            countdown=RECEIPT_CHECK_DELAY_SECONDS,
        )
    return len(tokens) - len(invalid)


@shared_task(**_RETRY_OPTIONS)
def check_push_receipts(*, tickets: dict[str, str]) -> int:
    """Sprawdza receipty Expo i kasuje martwe urządzenia (#315, ADR 0037).

    Mapa `ticket → token` jedzie w argumentach zadania — bez nowego modelu.
    Zwraca liczbę skasowanych urządzeń.
    """
    from apps.notifications.models import PushDevice
    from core.integrations.push.base import PushProviderError
    from core.integrations.push.registry import get_provider

    try:
        invalid = get_provider().check_receipts(tickets)
    except PushProviderTransientError:
        raise
    except PushProviderError:
        logger.exception("Nie udało się sprawdzić receiptów push")
        return 0
    if not invalid:
        return 0
    deleted, _ = PushDevice.objects.filter(token__in=invalid).delete()
    return deleted


@shared_task
def announce_promotion(*, promotion_id: str) -> int:
    """Ogłoszenie promocji w tle — akcja panelu kolejkuje je raz (#203).

    Ochronę przed podwójnym ogłoszeniem trzyma `Promotion.announced_at`
    ustawiane przed zakolejkowaniem (`queue_promotion_announcement`).
    """
    from apps.notifications.newsletter import send_promotion_announcement
    from apps.promotions.models import Promotion

    promotion = Promotion.objects.filter(pk=promotion_id).first()
    if promotion is None:
        return 0
    return send_promotion_announcement(promotion)
