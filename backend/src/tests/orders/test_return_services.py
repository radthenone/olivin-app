"""Zgłoszenie zwrotu: terminy, wyłączenia, flagi i decyzja per pozycja (#196)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from freezegun import freeze_time

from apps.inventory.models import StockMovement, StockMovementReason
from apps.notifications.models import Notification, NotificationKind
from apps.orders.models import (
    ClaimRequest,
    OrderStatus,
    ReturnItemStatus,
    ReturnReason,
    ReturnRequestStatus,
)
from apps.orders.services.returns import (
    ReturnLine,
    create_return_request,
    decide_return_item,
    return_options,
)
from tests.factories.orders import OrderFactory, OrderItemFactory
from tests.factories.products import (
    MadeToOrderProductFactory,
    ProductFactory,
    ProductVariantFactory,
    stock,
)

DELIVERED = "2027-03-01 12:00:00+01:00"


def _delivered_order(**kwargs):
    """Zamówienie doręczone w chwili `DELIVERED` — od niej biegną terminy."""
    with freeze_time(DELIVERED):
        return OrderFactory(status=OrderStatus.DELIVERED, **kwargs)


def _item(order, **kwargs):
    kwargs.setdefault("variant", ProductVariantFactory())
    return OrderItemFactory(order=order, **kwargs)


def _made_to_order_item(order, **kwargs):
    variant = ProductVariantFactory(product=MadeToOrderProductFactory())
    return _item(order, variant=variant, is_made_to_order=True, **kwargs)


def _request(order, reason, *lines: ReturnLine):
    return create_return_request(order, reason=reason, lines=list(lines))


@pytest.mark.django_db
class TestReturnDeadlines:
    """Terminy liczone od `Order.delivered_at` na zamrożonym czasie."""

    @pytest.mark.parametrize(
        ("reason", "last_moment", "too_late"),
        [
            (
                ReturnReason.WITHDRAWAL,
                "2027-03-15 23:59:59+01:00",
                "2027-03-16 00:00:00+01:00",
            ),
            (
                ReturnReason.GOODWILL,
                # Po zmianie czasu 28 marca koniec dnia liczy się w CEST.
                "2027-03-31 23:59:59+02:00",
                "2027-04-01 00:00:00+02:00",
            ),
            (
                ReturnReason.COMPLAINT,
                "2029-03-01 23:59:59+01:00",
                "2029-03-02 00:00:00+01:00",
            ),
        ],
    )
    def test_request_allowed_until_deadline_and_rejected_after(
        self, reason, last_moment, too_late
    ):
        """Termin trwa do końca ostatniego dnia czasu polskiego, nie co do sekundy."""
        order = _delivered_order()
        item = _item(order)
        claim = ClaimRequest.REFUND if reason == ReturnReason.COMPLAINT else ""

        with freeze_time(too_late):
            with pytest.raises(ValidationError):
                _request(order, reason, ReturnLine(item, 1, claim))

        with freeze_time(last_moment):
            request = _request(order, reason, ReturnLine(item, 1, claim))

        assert request.reason == reason

    def test_evening_delivery_counts_polish_calendar_day(self):
        """Doręczenie o 23:30 czasu polskiego (22:30 UTC) liczy się od tego dnia."""
        with freeze_time("2027-03-01 22:30:00+00:00"):
            order = OrderFactory(status=OrderStatus.DELIVERED)
        item = _item(order)

        with freeze_time("2027-03-16 00:00:00+01:00"), pytest.raises(ValidationError):
            _request(order, ReturnReason.WITHDRAWAL, ReturnLine(item, 1))
        with freeze_time("2027-03-15 23:59:59+01:00"):
            request = _request(order, ReturnReason.WITHDRAWAL, ReturnLine(item, 1))

        assert request.reason == ReturnReason.WITHDRAWAL

    def test_complaint_deadline_is_two_calendar_years_from_leap_day(self):
        """Doręczenie 29 lutego: termin reklamacji kończy się 28 lutego."""
        with freeze_time("2028-02-29 10:00:00+01:00"):
            order = OrderFactory(status=OrderStatus.DELIVERED)
        item = _item(order)

        options = return_options(order, now=order.delivered_at)

        deadline = options[0].deadlines[ReturnReason.COMPLAINT]
        assert (deadline.year, deadline.month, deadline.day) == (2030, 2, 28)
        assert item.pk == options[0].item.pk

    def test_options_count_taken_quantity_in_one_query(
        self, django_assert_max_num_queries
    ):
        """Ilość do zwrotu dla wszystkich pozycji bez zapytania na pozycję."""
        order = _delivered_order()
        items = [_item(order, quantity=2) for _ in range(3)]
        with freeze_time("2027-03-02"):
            _request(order, ReturnReason.GOODWILL, ReturnLine(items[0], 1))

        with freeze_time("2027-03-03"), django_assert_max_num_queries(2):
            options = return_options(order)

        assert [option.returnable_quantity for option in options] == [1, 2, 2]

    def test_options_list_only_reasons_still_open(self):
        """Po 14 dniach formularz nie proponuje już odstąpienia."""
        order = _delivered_order()
        _item(order)

        with freeze_time("2027-03-20 12:00:00+01:00"):
            options = return_options(order)

        assert set(options[0].deadlines) == {
            ReturnReason.GOODWILL,
            ReturnReason.COMPLAINT,
        }


@pytest.mark.django_db
class TestReturnEligibility:
    """Kto i co może zwrócić."""

    @pytest.mark.parametrize(
        "status",
        [OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.CANCELLED],
    )
    def test_only_delivered_order_accepts_request(self, status):
        """Odstąpienie przed doręczeniem obsługuje sklep poza systemem."""
        order = OrderFactory(status=status)
        item = _item(order)

        with pytest.raises(ValidationError):
            _request(order, ReturnReason.GOODWILL, ReturnLine(item, 1))

    def test_options_empty_for_undelivered_order(self):
        """Zamówienie w drodze nie ma czego zwracać."""
        order = OrderFactory(status=OrderStatus.SHIPPED)
        _item(order)

        assert return_options(order) == []

    def test_reason_is_required(self):
        """Podstawa zwrotu jest obowiązkowa."""
        order = _delivered_order()
        item = _item(order)

        with freeze_time("2027-03-02"), pytest.raises(ValidationError):
            _request(order, "", ReturnLine(item, 1))

    def test_item_from_another_order_is_rejected(self):
        """Zgłoszenie obejmuje wyłącznie pozycje swojego zamówienia."""
        order = _delivered_order()
        foreign = _item(_delivered_order())

        with freeze_time("2027-03-02"), pytest.raises(ValidationError):
            _request(order, ReturnReason.GOODWILL, ReturnLine(foreign, 1))

    def test_quantity_cannot_exceed_what_is_left_to_return(self):
        """Druga próba zwrotu tych samych sztuk jest odrzucana."""
        order = _delivered_order()
        item = _item(order, quantity=2)

        with freeze_time("2027-03-02"):
            _request(order, ReturnReason.GOODWILL, ReturnLine(item, 2))
            with pytest.raises(ValidationError):
                _request(order, ReturnReason.GOODWILL, ReturnLine(item, 1))

    def test_rejected_item_frees_quantity_for_another_request(self):
        """Odrzucona pozycja nie blokuje kolejnego zgłoszenia na inną podstawę."""
        order = _delivered_order()
        item = _item(order)

        with freeze_time("2027-03-02"):
            first = _request(order, ReturnReason.GOODWILL, ReturnLine(item, 1))
            decide_return_item(
                first.items.get(),
                status=ReturnItemStatus.REJECTED,
                note="Ślady użytkowania",
            )
            second = _request(
                order,
                ReturnReason.COMPLAINT,
                ReturnLine(item, 1, ClaimRequest.REFUND),
            )

        assert second.items.count() == 1

    def test_pair_returns_as_a_whole(self):
        """Para obrączek to jedna pozycja — nie da się zwrócić części sztuk."""
        order = _delivered_order()
        pair = _made_to_order_item(order, quantity=2, size="12", second_size="14")

        with freeze_time("2027-03-02"):
            with pytest.raises(ValidationError):
                _request(order, ReturnReason.GOODWILL, ReturnLine(pair, 1))
            request = _request(order, ReturnReason.GOODWILL, ReturnLine(pair, 2))

        assert request.items.get().quantity == 2


@pytest.mark.django_db
class TestWithdrawalExclusions:
    """Odstąpienie wyłączone dla grawerunku i produktu na zamówienie."""

    def test_withdrawal_rejected_for_engraved_item(self):
        """Grawer czyni wyrób zindywidualizowanym (ADR 0018)."""
        order = _delivered_order()
        item = _item(order, engraving_text="Na zawsze", engraving_price=5000)

        with freeze_time("2027-03-02"), pytest.raises(ValidationError):
            _request(order, ReturnReason.WITHDRAWAL, ReturnLine(item, 1))

    def test_withdrawal_rejected_for_made_to_order_item(self):
        """Produkt na zamówienie też jest zindywidualizowany (ADR 0024)."""
        order = _delivered_order()
        item = _made_to_order_item(order)

        with freeze_time("2027-03-02"), pytest.raises(ValidationError):
            _request(order, ReturnReason.WITHDRAWAL, ReturnLine(item, 1))

    def test_options_hide_withdrawal_for_engraved_item(self):
        """Formularz nie proponuje odstąpienia dla pozycji z grawerunkiem."""
        order = _delivered_order()
        _item(order, engraving_text="Na zawsze", engraving_price=5000)

        with freeze_time("2027-03-02"):
            options = return_options(order)

        assert ReturnReason.WITHDRAWAL not in options[0].deadlines

    def test_complaint_allowed_for_engraved_item(self):
        """Wada wyrobu grawerowanego podlega reklamacji na zasadach ogólnych."""
        order = _delivered_order()
        item = _item(order, engraving_text="Na zawsze", engraving_price=5000)

        with freeze_time("2027-03-02"):
            request = _request(
                order,
                ReturnReason.COMPLAINT,
                ReturnLine(item, 1, ClaimRequest.REFUND),
            )

        assert request.items.get().status == ReturnItemStatus.PENDING

    def test_engraved_item_outside_complaint_goes_to_agreement(self):
        """Zwrot dobrowolny grawerowanego wyrobu sklep uzgadnia z klientem."""
        order = _delivered_order()
        item = _item(order, engraving_text="Na zawsze", engraving_price=5000)

        with freeze_time("2027-03-02"):
            request = _request(order, ReturnReason.GOODWILL, ReturnLine(item, 1))

        assert request.items.get().status == ReturnItemStatus.TO_AGREE


@pytest.mark.django_db
class TestClaimRequests:
    """Żądanie reklamacyjne zależy od flag produktu."""

    def _complaint(self, product, claim):
        order = _delivered_order()
        item = _item(order, variant=ProductVariantFactory(product=product))
        with freeze_time("2027-03-02"):
            return _request(order, ReturnReason.COMPLAINT, ReturnLine(item, 1, claim))

    def test_refund_always_available(self):
        """Zwrot pieniędzy przysługuje zawsze."""
        request = self._complaint(ProductFactory(), ClaimRequest.REFUND)

        assert request.items.get().claim_request == ClaimRequest.REFUND

    @pytest.mark.parametrize(
        ("claim", "flag"),
        [
            (ClaimRequest.REPAIR, "repair_available"),
            (ClaimRequest.REPLACEMENT, "replacement_available"),
        ],
    )
    def test_repair_and_replacement_need_product_flag(self, claim, flag):
        """Naprawa i wymiana tylko, gdy produkt je dopuszcza."""
        with pytest.raises(ValidationError):
            self._complaint(ProductFactory(), claim)

        request = self._complaint(ProductFactory(**{flag: True}), claim)

        assert request.items.get().claim_request == claim

    def test_complaint_requires_claim_request(self):
        """Reklamacja bez wybranego żądania jest odrzucana."""
        with pytest.raises(ValidationError):
            self._complaint(ProductFactory(), "")

    def test_claim_request_only_with_complaint(self):
        """Żądanie reklamacyjne nie ma sensu przy innej podstawie."""
        order = _delivered_order()
        item = _item(order)

        with freeze_time("2027-03-02"), pytest.raises(ValidationError):
            _request(
                order,
                ReturnReason.GOODWILL,
                ReturnLine(item, 1, ClaimRequest.REFUND),
            )

    def test_options_list_claim_requests_from_flags(self):
        """Formularz pokazuje wyłącznie żądania dopuszczone przez produkt."""
        order = _delivered_order()
        product = ProductFactory(repair_available=True)
        _item(order, variant=ProductVariantFactory(product=product))

        with freeze_time("2027-03-02"):
            options = return_options(order)

        assert options[0].claim_requests == [ClaimRequest.REFUND, ClaimRequest.REPAIR]


@pytest.mark.django_db
class TestItemDecision:
    """Rozstrzygnięcie w panelu — osobno dla każdej pozycji."""

    def _goodwill(self, order, *items):
        with freeze_time("2027-03-02"):
            return _request(
                order,
                ReturnReason.GOODWILL,
                *(ReturnLine(item, item.quantity) for item in items),
            )

    def test_accepted_item_back_in_stock_creates_return_movement(self):
        """„Wraca na stan” zapisuje ruch `return` na wariancie."""
        order = _delivered_order()
        item = _item(order, quantity=2)
        inventory = stock(item.variant, 5)
        request = self._goodwill(order, item)

        decide_return_item(
            request.items.get(), status=ReturnItemStatus.ACCEPTED, restock=True
        )

        movement = StockMovement.objects.get(
            item=inventory, reason=StockMovementReason.RETURN
        )
        assert movement.quantity == 2
        assert order.number in movement.note

    def test_accepted_item_not_back_in_stock_leaves_stock(self):
        """„Nie wraca” nie rusza stanu."""
        order = _delivered_order()
        item = _item(order)
        stock(item.variant, 5)
        request = self._goodwill(order, item)

        decide_return_item(
            request.items.get(), status=ReturnItemStatus.ACCEPTED, restock=False
        )

        assert not StockMovement.objects.filter(
            reason=StockMovementReason.RETURN
        ).exists()

    def test_made_to_order_item_never_goes_back_to_stock(self):
        """Produkt na zamówienie nie ma stanu — nie może na niego wrócić."""
        order = _delivered_order()
        item = _made_to_order_item(order)
        request = self._goodwill(order, item)

        with pytest.raises(ValidationError):
            decide_return_item(
                request.items.get(), status=ReturnItemStatus.ACCEPTED, restock=True
            )

    def test_engraved_item_never_goes_back_to_stock(self):
        """Grawerowany egzemplarz przestaje być zamienny (ADR 0018)."""
        order = _delivered_order()
        item = _item(order, engraving_text="Na zawsze", engraving_price=5000)
        stock(item.variant, 5)
        request = self._goodwill(order, item)

        with pytest.raises(ValidationError):
            decide_return_item(
                request.items.get(),
                status=ReturnItemStatus.ACCEPTED,
                restock=True,
                agreed_resolution="Odkup po cenie złomu",
                agreed_amount=30000,
            )

    def test_agreement_needs_resolution_and_amount(self):
        """Pozycja „do uzgodnienia” wymaga wpisania formy i kwoty."""
        order = _delivered_order()
        item = _item(order, engraving_text="Na zawsze", engraving_price=5000)
        request = self._goodwill(order, item)
        return_item = request.items.get()

        with pytest.raises(ValidationError):
            decide_return_item(return_item, status=ReturnItemStatus.ACCEPTED)

        decide_return_item(
            return_item,
            status=ReturnItemStatus.ACCEPTED,
            agreed_resolution="Odkup po cenie złomu",
            agreed_amount=30000,
        )
        return_item.refresh_from_db()
        assert return_item.agreed_amount == 30000
        assert return_item.agreed_resolution == "Odkup po cenie złomu"

    def test_rejection_requires_justification(self):
        """Odrzucenie reklamacji bez uzasadnienia jest niedozwolone."""
        order = _delivered_order()
        item = _item(order)
        with freeze_time("2027-03-02"):
            request = _request(
                order,
                ReturnReason.COMPLAINT,
                ReturnLine(item, 1, ClaimRequest.REFUND),
            )
        return_item = request.items.get()

        with pytest.raises(ValidationError):
            decide_return_item(return_item, status=ReturnItemStatus.REJECTED)

        decide_return_item(
            return_item,
            status=ReturnItemStatus.REJECTED,
            note="Uszkodzenie mechaniczne przez klienta, nie wada",
        )
        return_item.refresh_from_db()
        assert return_item.status == ReturnItemStatus.REJECTED

    def test_decided_item_cannot_be_decided_again(self):
        """Decyzja jest ostateczna — ruch magazynowy nie może się zdublować."""
        order = _delivered_order()
        item = _item(order)
        stock(item.variant, 5)
        request = self._goodwill(order, item)
        return_item = request.items.get()
        decide_return_item(return_item, status=ReturnItemStatus.ACCEPTED, restock=True)

        with pytest.raises(ValidationError):
            decide_return_item(
                return_item, status=ReturnItemStatus.ACCEPTED, restock=True
            )

    def test_items_are_decided_separately(self):
        """Jedna pozycja przyjęta, druga odrzucona — zgłoszenie rozpatrzone."""
        order = _delivered_order()
        first, second = _item(order), _item(order)
        request = self._goodwill(order, first, second)
        accepted, rejected = request.items.order_by("id")

        decide_return_item(accepted, status=ReturnItemStatus.ACCEPTED)
        request.refresh_from_db()
        assert request.status == ReturnRequestStatus.SUBMITTED

        decide_return_item(
            rejected, status=ReturnItemStatus.REJECTED, note="Ślady użytkowania"
        )
        request.refresh_from_db()
        assert request.status == ReturnRequestStatus.RESOLVED
        order.refresh_from_db()
        assert order.status == OrderStatus.DELIVERED

    def test_last_decision_resolves_request_and_returns_order(self):
        """Ostatnia decyzja rozstrzyga zgłoszenie i przenosi zamówienie w `returned`."""
        order = _delivered_order()
        request = self._goodwill(order, _item(order), _item(order))
        first, second = request.items.order_by("id")

        decide_return_item(first, status=ReturnItemStatus.ACCEPTED)
        order.refresh_from_db()
        assert order.status == OrderStatus.DELIVERED

        decide_return_item(second, status=ReturnItemStatus.ACCEPTED)
        request.refresh_from_db()
        order.refresh_from_db()
        assert request.status == ReturnRequestStatus.RESOLVED
        assert order.status == OrderStatus.RETURNED

    @pytest.mark.parametrize(
        ("engraved", "status", "note"),
        [
            (False, ReturnItemStatus.ACCEPTED, ""),
            (True, ReturnItemStatus.REJECTED, "Brak porozumienia"),
        ],
    )
    def test_agreement_fields_only_when_accepting_item_to_agree(
        self, engraved, status, note
    ):
        """Forma i kwota uzgodnienia należą wyłącznie do przyjęcia „do uzgodnienia”."""
        order = _delivered_order()
        engraving = {"engraving_text": "Na zawsze", "engraving_price": 5000}
        item = _item(order, **(engraving if engraved else {}))
        request = self._goodwill(order, item)

        with pytest.raises(ValidationError):
            decide_return_item(
                request.items.get(),
                status=status,
                note=note,
                agreed_resolution="Odkup po cenie złomu",
                agreed_amount=30000,
            )

    def test_order_returned_when_accepted_returns_cover_all_items(self):
        """Zamówienie przechodzi w `returned`, gdy wróciło wszystko."""
        order = _delivered_order()
        item = _item(order)
        request = self._goodwill(order, item)

        decide_return_item(request.items.get(), status=ReturnItemStatus.ACCEPTED)

        order.refresh_from_db()
        assert order.status == OrderStatus.RETURNED


@pytest.mark.django_db
class TestReturnNotifications:
    """Transakcyjne powiadomienie o zmianie stanu zgłoszenia."""

    def test_created_and_resolved_request_notify_customer(
        self, django_capture_on_commit_callbacks
    ):
        """Klient dostaje wiadomość przy złożeniu i przy rozpatrzeniu."""
        order = _delivered_order()
        # Druga pozycja zostaje w zamówieniu — bez niej przyjęcie przeniosłoby
        # zamówienie w `returned` i doszłoby powiadomienie o jego statusie.
        item, _ = _item(order), _item(order)

        with patch("apps.notifications.services.send_notification_email") as send:
            with django_capture_on_commit_callbacks(execute=True):
                with freeze_time("2027-03-02"):
                    request = _request(
                        order, ReturnReason.GOODWILL, ReturnLine(item, 1)
                    )
            with django_capture_on_commit_callbacks(execute=True):
                decide_return_item(
                    request.items.get(), status=ReturnItemStatus.ACCEPTED
                )

        notifications = Notification.objects.filter(
            user=order.user, kind=NotificationKind.RETURN_REQUEST_STATUS_CHANGED
        )
        assert notifications.count() == 2
        # Przyjęcie rozlicza zwrot (#197): dochodzi e-mail o rozliczeniu
        # i o gotowej korekcie — każdy dokładnie raz, wszystkie na adres z zamówienia.
        subjects = sorted(call.kwargs["subject"] for call in send.call_args_list)
        assert subjects == sorted(
            [
                f"Zgłoszenie zwrotu do zamówienia {order.number}",
                f"Zgłoszenie zwrotu do zamówienia {order.number}",
                f"Rozliczenie zwrotu do zamówienia {order.number}",
                f"Dokument do zamówienia {order.number} gotowy",
            ]
        )
        assert send.call_count == 4
        assert all(call.kwargs["to"] == order.email for call in send.call_args_list)
