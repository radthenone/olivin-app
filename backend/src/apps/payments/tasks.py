from __future__ import annotations

from celery import shared_task

from apps.payments.services import refund_return
from core.integrations.payments import PaymentProviderError


@shared_task(
    autoretry_for=(PaymentProviderError,),
    retry_backoff=True,
    retry_backoff_max=3600,
    max_retries=10,
)
def refund_return_request(return_request_id: str) -> None:
    """Zwrot pieniężnej części rozliczenia; brak odpowiedzi operatora ponawia.

    Ponowienie idzie tym samym kluczem idempotencji, więc zwrot, który
    operator wykonał mimo przekroczenia czasu, nie powstanie drugi raz.
    Po wyczerpaniu prób zgłoszenie zostaje `pending` — do wyjaśnienia
    w panelu operatora, nie do przelewu w ciemno.
    """
    refund_return(return_request_id)
