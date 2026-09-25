"""Rozliczenie przyjętego zwrotu: najpierw kupon, reszta pieniędzmi (ADR 0031, #197)."""

from __future__ import annotations

from typing import Any

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser
from apps.notifications.models import Notification, NotificationKind
from apps.orders.admin import ReturnRequestAdmin
from apps.orders.models import (
    ClaimRequest,
    OrderStatus,
    ReturnItemStatus,
    ReturnReason,
    ReturnRefundStatus,
    ReturnRequest,
    SalesDocument,
    SalesDocumentKind,
)
from apps.orders.services.returns import (
    ReturnLine,
    create_return_request,
    decide_return_item,
)
from apps.orders.services.settlement import split_compensation
from apps.orders.tasks import issue_return_correction
from apps.payments.models import Payment, PaymentStatus
from apps.payments.services import handle_event
from apps.promotions.models import Coupon, CouponSource
from core.integrations.payments import EventKind, ProviderEvent
from tests.orders.test_sales_documents import _stored_pdf
from tests.factories.orders import OrderFactory, OrderItemFactory
from tests.factories.products import ProductFactory, ProductVariantFactory

DELIVERED = "2027-03-01 12:00:00+01:00"
LATER = "2027-03-05 12:00:00+01:00"
SHIPPING = 2000


def _order(*prices: int, coupon: int = 20000, user=None):
    """Doręczone zamówienie z pozycjami po jednej sztuce, kuponem i zapłatą.

    Część pieniężna (towar − kupon + dostawa) jest opłacona jedną płatnością,
    jak po zdarzeniu `payment_succeeded`.
    """
    kwargs = {"user": user} if user is not None else {}
    with freeze_time(DELIVERED):
        order = OrderFactory(
            status=OrderStatus.DELIVERED,
            shipping_cost=SHIPPING,
            coupon_amount=coupon,
            **kwargs,
        )
    items = [OrderItemFactory(order=order, unit_price=price) for price in prices]
    Payment.objects.create(
        order=order,
        intent_id=f"pi_{order.number}",
        amount=order.total.amount,
        currency="PLN",
        status=PaymentStatus.SUCCEEDED,
    )
    return order, items


def _return(order, reason, *items, status_=ReturnItemStatus.ACCEPTED, **decision):
    """Zgłoszenie całych pozycji i decyzja o każdej — w terminie."""
    with freeze_time(LATER):
        request = create_return_request(
            order,
            reason=reason,
            lines=[
                ReturnLine(
                    item,
                    item.quantity,
                    ClaimRequest.REFUND if reason == ReturnReason.COMPLAINT else "",
                )
                for item in items
            ],
        )
        for return_item in request.items.all():  # type: ignore[missing-attribute]
            note = "Ślady użytkowania" if status_ == ReturnItemStatus.REJECTED else ""
            decide_return_item(return_item, status=status_, note=note, **decision)
    request.refresh_from_db()
    return request


def _refunds(fake_payment_provider) -> list[int]:
    return [refund["amount"] for refund in fake_payment_provider.refunds]


@pytest.mark.unit
class TestSplitCompensation:
    """Podział kwoty na kupon i pieniądze — przykłady z ADR 0031."""

    @pytest.mark.parametrize(
        ("amount", "coupon_left", "expected"),
        [
            (18000, 20000, (18000, 0)),
            (25000, 20000, (20000, 5000)),
            (30000, 20000, (20000, 10000)),
            (18500, 20000, (19000, 0)),
            (18000, 0, (0, 18000)),
        ],
    )
    def test_adr_examples(self, amount, coupon_left, expected):
        """Zamówienie 300 zł (200 kuponem): zwrot 180 / 250 / 300 / 185 zł i bez kuponu."""
        assert split_compensation(amount, coupon_left) == expected

    def test_coupon_never_exceeds_what_is_left(self):
        """Zaokrąglenie w górę zatrzymuje się na pozostałej kuponowej części."""
        assert split_compensation(18500, 18000) == (18000, 500)

    def test_left_part_not_multiple_of_ten_goes_down_rest_as_money(self):
        """Nominał to wielokrotność 10 zł — resztę pozostałej części oddają pieniądze."""
        assert split_compensation(15010, 15037) == (15000, 10)
        assert split_compensation(5000, 700) == (0, 5000)


@pytest.mark.django_db
class TestSettleReturn:
    """Przyjęty zwrot wydaje kupon i zleca zwrot pieniędzy przez operatora."""

    @pytest.mark.parametrize(
        ("prices", "returned", "reason", "coupon", "money"),
        [
            ((18000, 10000), 1, ReturnReason.GOODWILL, 18000, 0),
            ((25000, 3000), 1, ReturnReason.GOODWILL, 20000, 5000),
            ((18500, 9500), 1, ReturnReason.GOODWILL, 19000, 0),
            # Odstąpienie od całości: 280 zł towaru + 20 zł dostawy = 300 zł.
            ((18000, 10000), 2, ReturnReason.WITHDRAWAL, 20000, 10000),
        ],
    )
    def test_adr_examples_on_order_of_300_with_200_coupon(
        self, fake_payment_provider, prices, returned, reason, coupon, money
    ):
        """Kupon ze źródłem `return` powiązany z zamówieniem, reszta zwrotem u operatora."""
        order, items = _order(*prices)

        request = _return(order, reason, *items[:returned])

        issued = Coupon.objects.get(source_order=order)
        assert issued.source == CouponSource.RETURN
        assert issued.nominal == coupon
        assert request.coupon == issued
        assert request.refund_amount == money
        assert _refunds(fake_payment_provider) == ([money] if money else [])
        assert request.refund_status == (
            ReturnRefundStatus.PENDING if money else ReturnRefundStatus.NONE
        )

    def test_coupon_valid_twelve_months(self):
        """Kupon ze zwrotu jest ważny 12 miesięcy od wydania."""
        order, items = _order(18000, 10000)

        _return(order, ReturnReason.GOODWILL, items[0])

        issued = Coupon.objects.get(source_order=order)
        assert (issued.expires_at.year, issued.expires_at.month) == (2028, 3)

    def test_two_returns_share_coupon_part(self, fake_payment_provider):
        """Drugi zwrot wyczerpuje tylko to, co zostało z kuponowej części."""
        order, items = _order(15000, 13000)

        first = _return(order, ReturnReason.WITHDRAWAL, items[0])
        second = _return(order, ReturnReason.WITHDRAWAL, items[1])

        assert first.coupon.nominal == 15000  # type: ignore[union-attr]
        assert first.refund_amount == 0
        # 130 zł towaru + 20 zł dostawy (odstąpienie objęło już wszystko).
        assert second.compensation_amount == 15000
        assert second.coupon.nominal == 5000  # type: ignore[union-attr]
        assert second.refund_amount == 10000
        assert _refunds(fake_payment_provider) == [10000]

    def test_order_without_coupon_gets_money_only(self, fake_payment_provider):
        """Kto płacił wyłącznie pieniędzmi, dostaje wyłącznie pieniądze."""
        order, items = _order(18000, 10000, coupon=0)

        request = _return(order, ReturnReason.GOODWILL, items[0])

        assert request.coupon is None
        assert not Coupon.objects.filter(source_order=order).exists()
        assert request.refund_amount == 18000
        assert _refunds(fake_payment_provider) == [18000]

    def test_value_after_promotion_without_shipping_for_partial_withdrawal(
        self, fake_payment_provider
    ):
        """Kwota to wartość pozycji po rabacie; dostawa tylko przy odstąpieniu od całości."""
        order, items = _order(18000, 10000, coupon=0)
        items[0].discount_amount = 3000
        items[0].save()

        request = _return(order, ReturnReason.WITHDRAWAL, items[0])

        assert request.compensation_amount == 15000
        assert _refunds(fake_payment_provider) == [15000]

    def test_agreed_amount_replaces_item_value(self, fake_payment_provider):
        """Pozycja do uzgodnienia rozlicza się uzgodnioną kwotą."""
        order, _ = _order(coupon=0)
        engraved = OrderItemFactory(
            order=order, unit_price=18000, engraving_text="Na zawsze"
        )
        order.payments.update(amount=order.total.amount)  # type: ignore[missing-attribute]

        request = _return(
            order,
            ReturnReason.GOODWILL,
            engraved,
            agreed_resolution="Odkup po cenie złomu",
            agreed_amount=6000,
        )

        assert request.compensation_amount == 6000
        assert _refunds(fake_payment_provider) == [6000]

    def test_repair_and_rejection_settle_nothing(self, fake_payment_provider):
        """Odrzucona pozycja i uwzględniona naprawa nie oddają pieniędzy ani kuponu."""
        order, items = _order(18000, 10000)
        items[0].variant = ProductVariantFactory(
            product=ProductFactory(repair_available=True)
        )
        items[0].save()

        rejected = _return(
            order, ReturnReason.GOODWILL, items[1], status_=ReturnItemStatus.REJECTED
        )
        with freeze_time(LATER):
            request = create_return_request(
                order,
                reason=ReturnReason.COMPLAINT,
                lines=[ReturnLine(items[0], 1, ClaimRequest.REPAIR)],
            )
            decide_return_item(
                request.items.get(),  # type: ignore[missing-attribute]
                status=ReturnItemStatus.ACCEPTED,
            )
        request.refresh_from_db()

        for settled in (rejected, request):
            assert settled.settled_at is None
            assert settled.refund_status == ReturnRefundStatus.NONE
        assert not Coupon.objects.exists()
        assert fake_payment_provider.refunds == []
        assert not SalesDocument.objects.filter(
            kind=SalesDocumentKind.CORRECTION
        ).exists()

    def test_full_return_marks_order_returned(self):
        """Zamówienie przechodzi w `returned`, gdy przyjęte zwroty objęły wszystko."""
        order, items = _order(18000, 10000)

        _return(order, ReturnReason.WITHDRAWAL, *items)

        order.refresh_from_db()
        assert order.status == OrderStatus.RETURNED


@pytest.mark.django_db
class TestRefundRefusal:
    """Odmowa operatora przenosi zgłoszenie do zwrotu ręcznego."""

    def test_provider_refusal_moves_to_manual(self, fake_payment_provider):
        """Operator odrzuca zlecenie — kupon zostaje, pieniądze do przelewu."""
        order, items = _order(25000, 3000)
        fake_payment_provider.fail_with = "card closed"

        request = _return(order, ReturnReason.GOODWILL, items[0])

        assert request.refund_status == ReturnRefundStatus.MANUAL
        assert request.refund_amount == 5000
        assert request.coupon.nominal == 20000  # type: ignore[union-attr]

    def test_refund_failed_event_moves_to_manual(self, fake_payment_provider):
        """Zwrot odrzucony później zdarzeniem — też do zwrotu ręcznego."""
        order, items = _order(18000, 10000, coupon=0)
        request = _return(order, ReturnReason.GOODWILL, items[0])

        handle_event(_refund_event(EventKind.REFUND_FAILED, request))

        request.refresh_from_db()
        assert request.refund_status == ReturnRefundStatus.MANUAL

    def test_refunded_event_completes_without_touching_payment(
        self, fake_payment_provider
    ):
        """Zwrot częściowy nie zamyka płatności ani zamówienia jak anulowanie."""
        order, items = _order(18000, 10000, coupon=0)
        request = _return(order, ReturnReason.GOODWILL, items[0])

        handle_event(_refund_event(EventKind.REFUNDED, request))

        request.refresh_from_db()
        order.refresh_from_db()
        assert request.refund_status == ReturnRefundStatus.REFUNDED
        assert order.payments.get().status == PaymentStatus.SUCCEEDED  # type: ignore[missing-attribute]
        assert order.status == OrderStatus.DELIVERED

    def test_admin_marks_manual_transfer(self, admin_user: CustomUser):
        """Sklep oznacza w panelu przelew wykonany ręcznie."""
        order, items = _order(25000, 3000)
        from core.integrations.payments.fake import FakePaymentProvider

        FakePaymentProvider.fail_with = "card closed"
        request = _return(order, ReturnReason.GOODWILL, items[0])
        FakePaymentProvider.fail_with = ""
        http = RequestFactory().post("/")
        http.user = admin_user
        http.session = {}  # type: ignore[assignment]
        http._messages = FallbackStorage(http)  # type: ignore[attr-defined]

        ReturnRequestAdmin(ReturnRequest, AdminSite()).mark_manual_refund_done(
            http, ReturnRequest.objects.all()
        )

        request.refresh_from_db()
        assert request.refund_status == ReturnRefundStatus.MANUAL_DONE


def _refund_event(kind: EventKind, request: ReturnRequest) -> ProviderEvent:
    return ProviderEvent(
        id=f"evt_{kind}_{request.refund_id}",
        kind=kind,
        type=str(kind),
        intent_id=request.order.payments.get().intent_id,  # type: ignore[missing-attribute]
        refund_id=request.refund_id,
    )


@pytest.mark.django_db
class TestCorrectionAndNotification:
    """Korekta raz po rozliczeniu i powiadomienie z kwotą i formą."""

    def test_correction_issued_once_per_settled_request(
        self, django_capture_on_commit_callbacks
    ):
        """Korekta powstaje po rozliczeniu; powtórka zadania nie nadaje numeru."""
        order, items = _order(25000, 3000)

        with django_capture_on_commit_callbacks(execute=True):
            request = _return(order, ReturnReason.GOODWILL, items[0])
        issue_return_correction(str(request.pk))

        correction = SalesDocument.objects.get(kind=SalesDocumentKind.CORRECTION)
        assert correction.order == order
        assert correction.return_request == request

    def test_correction_names_corrected_document_and_amounts(self, monkeypatch):
        """Korekta wskazuje dokument korygowany, przyczynę, pozycje i dostawę."""
        from apps.orders.services import document as documents

        rendered: list[str] = []
        original = documents.render_to_string

        def capture(*args, **kwargs):
            html = original(*args, **kwargs)
            rendered.append(html)
            return html

        monkeypatch.setattr(documents, "render_to_string", capture)
        order, items = _order(18000, 10000)
        confirmation = documents.issue_document(order, SalesDocumentKind.CONFIRMATION)
        request = _return(order, ReturnReason.WITHDRAWAL, *items)

        correction = documents.issue_correction(request)

        assert correction is not None
        html = rendered[-1]
        assert f"Korekta do: Potwierdzenie zamówienia {confirmation.reference}" in html
        assert "Odstąpienie od umowy" in html
        assert "−20.00 PLN" in html  # dostawa
        assert "Razem korekta" in html
        assert "−300.00 PLN" in html
        assert _stored_pdf(correction.object_key).startswith(b"%PDF")

    def test_notification_with_amount_and_form(
        self, user: CustomUser, django_capture_on_commit_callbacks
    ):
        """Transakcyjne powiadomienie mówi, ile kuponem, ile pieniędzmi."""
        order, items = _order(25000, 3000, user=user)

        with django_capture_on_commit_callbacks(execute=True):
            request = _return(order, ReturnReason.GOODWILL, items[0])

        notification = Notification.objects.get(
            user=user, kind=NotificationKind.RETURN_SETTLED
        )
        assert notification.data["coupon_code"] == request.coupon.code  # type: ignore[union-attr]
        assert "200.00 PLN" == notification.data["coupon_amount"]
        assert "50.00 PLN" == notification.data["refund_amount"]


@pytest.mark.django_db
class TestSettlementApi:
    """API pokazuje rozliczenie: kupon z kodem, pieniądze i ich status."""

    def test_detail_shows_coupon_money_and_refund_status(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        """Klient widzi kod kuponu, kwoty i stan zwrotu pieniędzy."""
        order, items = _order(25000, 3000, user=user)
        request = _return(order, ReturnReason.GOODWILL, items[0])

        response: Any = authenticated_client.get(
            reverse("order-return-detail", args=[order.number, request.pk])
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["couponCode"] == request.coupon.code  # type: ignore[union-attr]
        assert data["couponAmount"]["amount"] == 20000
        assert data["refundAmount"]["amount"] == 5000
        assert data["compensationAmount"]["amount"] == 25000
        assert data["refundStatus"] == ReturnRefundStatus.PENDING
