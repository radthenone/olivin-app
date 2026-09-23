"""Serializer składania zamówienia — przejście z danych żądania na typy domeny."""

from __future__ import annotations

import pytest

from apps.orders.serializers import OrderCreateSerializer
from apps.orders.services import ShippingAddress
from tests.factories.shipping import ShippingMethodFactory


@pytest.mark.django_db
class TestOrderCreateSerializerToAddress:
    def test_returns_shipping_address_with_country_code(self):
        """Adres wychodzi jako `ShippingAddress`, a kraj jako goły kod ISO."""
        method = ShippingMethodFactory()
        payload = OrderCreateSerializer(
            data={
                "recipient_name": "Anna Nowak",
                "street": "Kwiatowa 1",
                "street2": "m. 2",
                "city": "Kraków",
                "postal_code": "30-001",
                "country": "PL",
                "shipping_method": method.pk,
            }
        )
        payload.is_valid(raise_exception=True)

        address = payload.to_address()

        assert address == ShippingAddress(
            recipient_name="Anna Nowak",
            street="Kwiatowa 1",
            street2="m. 2",
            city="Kraków",
            postal_code="30-001",
            country="PL",
        )
        assert type(address.country) is str
