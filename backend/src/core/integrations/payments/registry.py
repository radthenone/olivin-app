from __future__ import annotations

from django.conf import settings
from django.utils.module_loading import import_string

from core.integrations.payments.base import PaymentProvider

DEFAULT_PROVIDER = "core.integrations.payments.stripe.StripeProvider"


def get_provider() -> PaymentProvider:
    """Operator płatności wskazany konfiguracją.

    Domyślnie Stripe — w środowisku roboczym z kluczem testowym. Atrapę
    trzeba wskazać jawnie, żeby pomyłka w konfiguracji produkcji nie
    zamieniła sklepu w taki, który „przyjmuje” płatności bez pieniędzy.
    """
    path = getattr(settings, "PAYMENT_PROVIDER", DEFAULT_PROVIDER)
    return import_string(path)()
