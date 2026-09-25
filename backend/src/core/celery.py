import os

from celery import Celery
from celery.signals import worker_ready

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


@worker_ready.connect
def refresh_exchange_rate_on_start(**kwargs) -> None:
    """Kurs euro zaraz po starcie workera — bez czekania na beat o 6:10.

    Zadanie jest idempotentne: przy świeżym kursie nic nie pobiera, więc
    restart workera nie odpytuje NBP bez potrzeby (ADR 0019).
    """
    app.send_task("apps.products.tasks.refresh_exchange_rate")
