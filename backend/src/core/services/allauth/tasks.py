from __future__ import annotations

from celery import shared_task
from pack_logger import log

from core.services.allauth.selectors import get_stale_unverified_users_queryset


@shared_task
def cleanup_stale_unverified_users() -> None:
    qs = get_stale_unverified_users_queryset()

    count = qs.count()
    if count > 0:
        log.info(f"Deleting {count} stale unverified users")
        qs.delete()