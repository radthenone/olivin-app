"""
Celery configuration.
"""

import os
from datetime import timedelta

from celery.schedules import crontab, schedule

# Celery
CELERY_BROKER_URL = str(
    os.environ.get("CELERY_BROKER_URL", "redis://olivin-redis:6379/0")
)
CELERY_RESULT_BACKEND = str(
    os.environ.get("CELERY_RESULT_BACKEND", "redis://olivin-redis:6379/0")
)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Europe/Warsaw"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# Django celery results
CELERY_RESULT_BACKEND = "django-db"
CELERY_RESULT_SERIALIZER = "json"
CELERY_CACHE_BACKEND = "django-cache"
CELERY_IMPORTS = (
    "core.services.mail.tasks",
    "core.services.allauth.tasks",
    "apps.products.tasks",
    "apps.translations.tasks",
    "apps.orders.tasks",
    "apps.inventory.tasks",
)

CELERY_BEAT_SCHEDULE = {
    "cleanup-stale-unverified-users": {
        "task": "core.services.allauth.tasks.cleanup_stale_unverified_users",
        "schedule": schedule(run_every=timedelta(days=1)),  # 1 day
    },
    # Raz w miesiącu, pierwszego dnia rano. Zadanie wstawia notowania jako
    # zaproponowane — cen nie zmienia, bo to robi dopiero aktywacja przez
    # właściciela (ADR 0022).
    # Drugi wyzwalacz obok publikacji: wyłapuje to, czego tamten nie
    # dowiózł — padnięte zadanie, tekst dopisany po publikacji, nowy język.
    "translate-published-catalog": {
        "task": "apps.translations.tasks.translate_published_catalog",
        "schedule": schedule(run_every=timedelta(hours=24)),
    },
    "propose-metal-rates": {
        "task": "apps.products.tasks.propose_metal_rates",
        "schedule": crontab(minute=0, hour=6, day_of_month=1),
    },
    # Co pięć minut: rezerwacja trzyma stan pół godziny, więc obchód częstszy
    # niczego nie poprawia, a rzadszy zostawiałby w panelu rezerwacje
    # „aktywne" długo po terminie. Dostępność i tak liczy sam termin.
    "expire-reservations": {
        "task": "apps.inventory.tasks.expire_reservations",
        "schedule": crontab(minute="*/5"),
    },
    # Raz na dobę, nad ranem: koszyk gościa bez aktywności przez 30 dni nie
    # ma już komu się pokazać, bo dostęp do niego daje wyłącznie token.
    "purge-stale-guest-carts": {
        "task": "apps.orders.tasks.purge_stale_guest_carts",
        "schedule": crontab(minute=30, hour=3),
    },
    # Co godzinę: zamówienie bez zapłaty przez dobę anuluje się samo
    # i zwalnia rezerwacje (`CONTEXT.md`, Order).
    "cancel-stale-orders": {
        "task": "apps.orders.tasks.cancel_stale_orders",
        "schedule": crontab(minute=15),
    },
}
