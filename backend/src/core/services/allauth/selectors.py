from __future__ import annotations

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, QuerySet


def get_stale_unverified_users_queryset() -> QuerySet:
    user_model = get_user_model()

    verified_email_exists = EmailAddress.objects.filter(
        user=OuterRef("pk"),
        verified=True,
    )

    return (
        user_model.objects
        .filter(
            last_login__isnull=True,
            is_superuser=False,
            is_staff=False,
        )
        .annotate(has_verified_email=Exists(verified_email_exists))
        .filter(has_verified_email=False)
    )
