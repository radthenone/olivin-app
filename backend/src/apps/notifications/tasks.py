from __future__ import annotations

import logging
from typing import Any

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def send_push_notification(
    self,
    *,
    user_id: str,
    title: str,
    body: str,
    data: dict[str, Any] | None = None,
) -> int:
    """Wysyła push na urządzenia klienta przez adapter (issue #202).

    Asynchronicznie: `notify()` kolejkuje to zadanie po commicie, a błąd
    pusha nie blokuje e-maila ani rekordu w aplikacji — zadanie łapie błąd
    dostawcy i kończy się cicho. Tokeny odrzucone przez Expo
    (`DeviceNotRegistered`) są kasowane, żeby nie strzelać w martwe urządzenia.
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
        invalid = get_provider().send_push(
            tokens=tokens, title=title, body=body, data=payload
        )
    except PushProviderError:
        logger.exception("Nie udało się wysłać pusha do klienta %s", user_id)
        return 0
    except Exception:
        logger.exception("Nieoczekiwany błąd wysyłki pusha do klienta %s", user_id)
        return 0
    if invalid:
        PushDevice.objects.filter(user_id=user_id, token__in=invalid).delete()
    else:
        PushDevice.objects.filter(user_id=user_id, token__in=tokens).update(
            last_used_at=timezone.now()
        )
    return len(tokens) - len(invalid)


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
