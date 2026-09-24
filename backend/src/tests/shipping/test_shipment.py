"""Przesyłka: ograniczenie w bazie, kwota i panel (`CONTEXT.md`, Shipment)."""

from __future__ import annotations

import pytest
from django.db.utils import IntegrityError
from django.test import Client
from django.urls import reverse

from apps.shipping.models import Shipment
from common.money import Money
from tests.factories.shipping import ShipmentFactory


@pytest.mark.django_db
class TestShipmentModel:
    def test_negative_declared_value_is_rejected_by_database(self):
        shipment = ShipmentFactory()

        with pytest.raises(IntegrityError):
            Shipment.objects.filter(pk=shipment.pk).update(declared_value=-1)

    def test_declared_value_comes_out_as_money(self):
        shipment = ShipmentFactory(declared_value=25000, currency="PLN")

        assert shipment.declared_value_money == Money(25000, "PLN")

    def test_str_is_tracking_number_once_shipped(self):
        assert str(ShipmentFactory(tracking_number="PL123")) == "PL123"

    def test_str_names_order_before_shipping(self):
        shipment = ShipmentFactory(tracking_number="")

        assert str(shipment) == f"Przesyłka do {shipment.order.pk}"


@pytest.mark.django_db
class TestShipmentAdmin:
    def test_changelist_opens_for_admin(self, admin_user):
        ShipmentFactory(tracking_number="PL123")
        client = Client()
        client.force_login(admin_user)

        response = client.get(reverse("admin:shipping_shipment_changelist"))

        assert response.status_code == 200
        assert b"PL123" in response.content
