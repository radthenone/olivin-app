"""Wspólne przygotowanie testów płatności: zamówienie złożone prawdziwą ścieżką."""

from __future__ import annotations

from apps.consents.models import ConsentKind
from apps.orders.models import Order
from apps.orders.services import ShippingAddress, create_order
from apps.orders.services.cart import add_item
from core.integrations.payments import EventKind
from core.integrations.payments.fake import event_payload, sign
from tests.factories.accounts import UserFactory
from tests.factories.consents import ConsentDocumentFactory, ConsentFactory
from tests.factories.orders import CartFactory
from tests.factories.products import (
    ProductVariantFactory,
    PublishedProductFactory,
    stock,
)
from tests.factories.shipping import ShippingMethodFactory

ADDRESS = ShippingAddress(
    recipient_name="Jan Kowalski",
    street="Złota 44",
    city="Warszawa",
    postal_code="00-120",
    country="PL",
)


def placed_order(*, user=None, quantity: int = 1, on_hand: int = 5) -> Order:
    """Zamówienie `pending` z rezerwacją, jak po kroku składania w kasie."""
    user = user or UserFactory()
    ConsentFactory(user=user, document=ConsentDocumentFactory(kind=ConsentKind.TERMS))
    cart = CartFactory(user=user)
    variant = ProductVariantFactory(product=PublishedProductFactory(), price=100000)
    stock(variant, on_hand)
    add_item(cart, variant=variant, quantity=quantity)
    return create_order(
        cart=cart,
        address=ADDRESS,
        shipping_method=ShippingMethodFactory(rate=1990),
        user=user,
    )


def signed_event(
    kind: EventKind, intent_id: str, event_id: str = ""
) -> tuple[bytes, str]:
    """Treść zdarzenia atrapy i jej podpis — gotowe do wysłania na webhook."""
    payload = event_payload(kind, intent_id, event_id)
    return payload, sign(payload)
