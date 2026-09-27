"""Dokumenty sprzedaży: numeracja, zadanie po zapłacie, PDF i API (ADR 0026)."""

from __future__ import annotations

import os
import threading
from datetime import date
from typing import Any

import boto3
import pytest
from django.db import connection, transaction
from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser
from apps.orders.models import (
    DocumentCounter,
    Order,
    OrderStatus,
    SalesDocument,
    SalesDocumentKind,
)
from apps.orders.services import issue_document, issue_documents, next_number
from apps.orders.services.cart import add_item
from apps.orders.services.document import render_pdf
from apps.orders.tasks import issue_sales_documents
from apps.payments.services import handle_event, start_payment
from core.integrations.payments import EventKind, ProviderEvent
from core.storage import DOCUMENTS
from tests.factories.consents import ConsentDocumentFactory, ConsentFactory
from tests.factories.orders import (
    CartFactory,
    GuestOrderFactory,
    OrderFactory,
    OrderItemFactory,
)
from tests.factories.products import (
    ProductVariantFactory,
    PublishedProductFactory,
    stock,
)
from tests.factories.shipping import ShippingMethodFactory
from tests.payments.helpers import placed_order

CONFIRMATION = SalesDocumentKind.CONFIRMATION
INVOICE = SalesDocumentKind.INVOICE


def _paid_order(**kwargs) -> Order:
    order = OrderFactory(status=OrderStatus.PAID, **kwargs)
    OrderItemFactory(order=order)
    return order


def _documents_url(number: str) -> str:
    return reverse("order-documents", args=[number])


def _stored_pdf(key: str) -> bytes:
    s3 = boto3.client("s3", region_name="us-east-1")
    return s3.get_object(Bucket=DOCUMENTS.name, Key=key)["Body"].read()


@pytest.mark.django_db
class TestDocumentNumbering:
    """Numeracja ciągła w obrębie rodzaju i roku."""

    def test_numbers_are_consecutive_within_kind_and_year(self):
        """Kolejne wywołania dają 1, 2, 3 — bez luk."""
        assert [next_number(CONFIRMATION, 2026) for _ in range(3)] == [1, 2, 3]

    def test_kinds_and_years_are_numbered_separately(self):
        """Faktura i nowy rok zaczynają własną numerację od jedynki."""
        next_number(CONFIRMATION, 2026)
        next_number(CONFIRMATION, 2026)

        assert next_number(INVOICE, 2026) == 1
        assert next_number(CONFIRMATION, 2027) == 1

    def test_rolled_back_issue_leaves_no_gap(self, monkeypatch):
        """Nieudany render cofa numer razem z dokumentem — następny nie ma luki."""
        order = _paid_order()

        def broken_render(document):
            raise RuntimeError("render padł")

        monkeypatch.setattr("apps.orders.services.document.render_pdf", broken_render)
        with pytest.raises(RuntimeError):
            issue_document(order, CONFIRMATION)
        monkeypatch.undo()

        document = issue_document(order, CONFIRMATION)

        assert document.number == 1
        assert DocumentCounter.objects.get(kind=CONFIRMATION).last_number == 1

    @freeze_time("2027-01-01 00:30:00+01:00")
    def test_year_comes_from_local_issue_date(self):
        """Po północy w Warszawie dokument należy już do nowego roku."""
        document = issue_document(_paid_order(), CONFIRMATION)

        assert document.issued_on == date(2027, 1, 1)
        assert document.year == 2027
        assert document.reference == "PZ 1/2027"


# Bez markera `integration`: ten wyłącza atrapę S3, a tu potrzebny jest
# wyłącznie żywy Postgres (`TEST_DATABASE=postgres` + `POSTGRES_*`).
@pytest.mark.skipif(
    os.environ.get("TEST_DATABASE") != "postgres",
    reason="blokady wierszy wymagają Postgresa: TEST_DATABASE=postgres",
)
@pytest.mark.django_db(transaction=True)
class TestDocumentNumberingConcurrency:
    """Równoległe nadawanie numerów na Postgresie — bez luki i bez duplikatu."""

    @staticmethod
    def _run_in_parallel(target, workers: int) -> list[Any]:
        barrier = threading.Barrier(workers)
        results: list[Any] = []
        errors: list[BaseException] = []
        lock = threading.Lock()

        def worker() -> None:
            try:
                barrier.wait()
                value = target()
                with lock:
                    results.append(value)
            except BaseException as error:  # noqa: BLE001 — zgłoszone niżej
                errors.append(error)
            finally:
                connection.close()

        threads = [threading.Thread(target=worker) for _ in range(workers)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert not errors, errors
        return results

    def test_parallel_calls_get_distinct_consecutive_numbers(self):
        """Osiem wątków naraz, pierwszy numer roku — numery 1..8, każdy raz."""

        def allocate() -> int:
            with transaction.atomic():
                return next_number(CONFIRMATION, 2026)

        numbers = self._run_in_parallel(allocate, workers=8)

        assert sorted(numbers) == list(range(1, 9))

    def test_parallel_task_runs_issue_one_document(self):
        """Dwa równoległe zadania dla jednego zamówienia wystawiają jeden dokument."""
        order = _paid_order()

        self._run_in_parallel(lambda: issue_sales_documents(str(order.pk)), workers=2)  # type: ignore[missing-argument]

        assert SalesDocument.objects.filter(order=order).count() == 1
        assert DocumentCounter.objects.get(kind=CONFIRMATION).last_number == 1


@pytest.mark.django_db
class TestIssueSalesDocumentsTask:
    """Zadanie po zapłacie i jego idempotencja."""

    def test_confirmation_is_issued_for_paid_order(self):
        """Opłacone zamówienie dostaje potwierdzenie, bez faktury."""
        order = _paid_order()

        references = issue_sales_documents(str(order.pk))  # type: ignore[missing-argument]

        assert references == ["PZ 1/" + str(date.today().year)]
        assert list(order.documents.values_list("kind", flat=True)) == [CONFIRMATION]  # type: ignore[missing-attribute]

    def test_invoice_is_issued_when_requested(self):
        """Prośba o fakturę dokłada fakturę imienną obok potwierdzenia."""
        order = _paid_order(invoice_requested=True)

        issue_sales_documents(str(order.pk))  # type: ignore[missing-argument]

        assert set(order.documents.values_list("kind", flat=True)) == {  # type: ignore[missing-attribute]
            CONFIRMATION,
            INVOICE,
        }

    def test_rerun_does_not_create_second_document(self):
        """Powtórka zadania zwraca te same dokumenty i nie zużywa numeru."""
        order = _paid_order(invoice_requested=True)

        first = issue_sales_documents(str(order.pk))  # type: ignore[missing-argument]
        second = issue_sales_documents(str(order.pk))  # type: ignore[missing-argument]

        assert first == second
        assert SalesDocument.objects.filter(order=order).count() == 2
        assert DocumentCounter.objects.get(kind=CONFIRMATION).last_number == 1

    def test_pending_order_gets_no_documents(self):
        """Nieopłacone zamówienie nie dostaje dokumentu."""
        order = OrderFactory(status=OrderStatus.PENDING)

        assert issue_documents(order) == []
        assert not SalesDocument.objects.exists()

    def test_successful_payment_triggers_task_after_commit(
        self, django_capture_on_commit_callbacks
    ):
        """Zdarzenie zapłaty uruchamia zadanie dopiero po zatwierdzeniu transakcji."""
        order = placed_order()
        started = start_payment(order)
        event = ProviderEvent(
            id="evt_paid",
            kind=EventKind.PAYMENT_SUCCEEDED,
            type=str(EventKind.PAYMENT_SUCCEEDED),
            intent_id=started.payment.intent_id,
        )

        with django_capture_on_commit_callbacks(execute=True):
            handle_event(event)

        assert SalesDocument.objects.filter(order=order, kind=CONFIRMATION).exists()

    def test_repeated_payment_event_does_not_issue_again(
        self, django_capture_on_commit_callbacks
    ):
        """Drugie zdarzenie zapłaty nie wystawia drugiego dokumentu."""
        order = placed_order()
        started = start_payment(order)
        event = ProviderEvent(
            id="evt_paid",
            kind=EventKind.PAYMENT_SUCCEEDED,
            type=str(EventKind.PAYMENT_SUCCEEDED),
            intent_id=started.payment.intent_id,
        )

        with django_capture_on_commit_callbacks(execute=True):
            handle_event(event)
            handle_event(event)

        assert SalesDocument.objects.filter(order=order).count() == 1


@pytest.mark.django_db
class TestSalesDocumentPdf:
    """Smoke renderu PDF z szablonu przez WeasyPrint."""

    def test_render_produces_pdf(self):
        """Render daje prawdziwy PDF, także z polskimi znakami w pozycji."""
        order = _paid_order()
        OrderItemFactory(order=order, product_name="Pierścionek z żółtego złota")
        document = SalesDocument(
            order=order,
            kind=INVOICE,
            number=7,
            year=2026,
            issued_on=date(2026, 9, 24),
        )

        pdf = render_pdf(document)

        assert pdf.startswith(b"%PDF")
        assert len(pdf) > 1000

    def test_issued_pdf_lands_in_documents_bucket(self):
        """Wystawiony dokument leży w buckecie `documents` pod zapisanym kluczem."""
        document = issue_document(_paid_order(), CONFIRMATION)

        assert document.object_key.endswith(".pdf")
        assert _stored_pdf(document.object_key).startswith(b"%PDF")


@pytest.mark.django_db
class TestOrderDocumentsApi:
    """`GET /orders/{number}/documents/` z adresami podpisanymi na czas."""

    def test_owner_lists_documents_with_signed_urls(
        self, authenticated_client: APIClient, user: CustomUser, settings
    ):
        """Właściciel dostaje listę z adresem podpisanym na czas."""
        order = _paid_order(user=user, invoice_requested=True)
        issue_documents(order)

        response: Any = authenticated_client.get(_documents_url(order.number))

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert [row["kind"] for row in body] == [CONFIRMATION, INVOICE]
        assert body[0]["reference"].startswith("PZ 1/")
        assert "X-Amz-Signature" in body[0]["url"]
        assert "X-Amz-Expires=" in body[0]["url"]

    def test_other_customer_gets_404(self, api_client: APIClient, user: CustomUser):
        """Cudzy klient nie widzi dokumentów zamówienia."""
        order = _paid_order(user=user)
        issue_documents(order)
        other = CustomUser.objects.create_user(
            email="inny@test.com", password="testpass123!"
        )
        api_client.force_authenticate(user=other)

        response: Any = api_client.get(_documents_url(order.number))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_guest_needs_order_email(self, api_client: APIClient):
        """Gość pobiera dokumenty numerem i adresem; sam numer nie wystarcza."""
        order = GuestOrderFactory(status=OrderStatus.PAID)
        OrderItemFactory(order=order)
        issue_documents(order)

        without_email: Any = api_client.get(_documents_url(order.number))
        with_email: Any = api_client.get(
            _documents_url(order.number), {"email": order.email}
        )

        assert without_email.status_code == status.HTTP_404_NOT_FOUND
        assert with_email.status_code == status.HTTP_200_OK
        assert len(with_email.json()) == 1

    def test_order_accepts_invoice_request(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        """Składający zamówienie może poprosić o fakturę imienną."""
        ConsentFactory(user=user, document=ConsentDocumentFactory(kind="terms"))
        cart = CartFactory(user=user)
        variant = ProductVariantFactory(product=PublishedProductFactory(), price=10000)
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)

        response: Any = authenticated_client.post(
            reverse("order-list"),
            {
                "recipientName": "Jan Kowalski",
                "street": "Złota 44",
                "city": "Warszawa",
                "postalCode": "00-120",
                "country": "PL",
                "shippingMethod": str(ShippingMethodFactory().pk),
                "invoiceRequested": True,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["invoiceRequested"] is True
        assert Order.objects.get(number=response.json()["number"]).invoice_requested
