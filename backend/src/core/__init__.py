"""Wczytanie aplikacji Celery razem z Django.

Bez tego `shared_task(...).delay()` wywołane z procesu Django — na przykład
z akcji w panelu — trafia do domyślnej aplikacji Celery, która nie zna
ustawień `CELERY_*`. Zadanie nie idzie wtedy do skonfigurowanego brokera,
tylko do `amqp://localhost`, i kończy się błędem połączenia. Worker
uruchamiany przez `celery -A core` importuje ten moduł sam, więc problem
widać dopiero po stronie aplikacji.
"""

from core.celery import app as celery_app

__all__ = ("celery_app",)
