from __future__ import annotations

from celery import shared_task
from django.utils import timezone

from apps.promotions.models import Coupon, CouponStatus


@shared_task
def expire_coupons() -> int:
    """Zamyka kupony po terminie ważności; zwraca ich liczbę.

    Sama ważność i tak liczy się z daty (`Coupon.is_usable`) — status jest
    dla panelu, żeby właściciel nie widział przeterminowanych jako wydanych.
    """
    return Coupon.objects.filter(
        status=CouponStatus.ISSUED, expires_at__lte=timezone.now()
    ).update(status=CouponStatus.EXPIRED)
