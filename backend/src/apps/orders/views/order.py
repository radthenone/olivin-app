from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Prefetch, QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotAuthenticated, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.orders.models import Order, OrderItem, OrderStatus
from apps.orders.schema import order_schema
from apps.orders.serializers import (
    OrderCreateSerializer,
    OrderLookupSerializer,
    OrderSerializer,
    ReturnOptionSerializer,
    ReturnRequestCreateSerializer,
    ReturnRequestSerializer,
    SalesDocumentSerializer,
)
from apps.orders.services import (
    cancel_order,
    create_order,
    is_covered_by_coupon,
    get_cart,
)
from apps.orders.services.returns import (
    ReturnLine,
    create_return_request,
)
from apps.orders.services.returns import return_options as build_return_options
from apps.orders.views.cart import token_of, user_of
from apps.payments.serializers import PaymentIntentSerializer
from apps.payments.services import request_cancellation, start_payment


@order_schema
class OrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """Zamówienia klienta i gościa.

    Actions:
    - list:     GET  /orders/                  — własne zamówienia zalogowanego
    - retrieve: GET  /orders/{number}/         — zalogowany własne, gość po `?email=`
    - create:   POST /orders/                  — złożenie zamówienia z koszyka
    - cancel:   POST /orders/{number}/cancel/  — anulowanie `pending` albo zwrot `paid`
    - payment:  POST /orders/{number}/payment/ — intencja płatnicza (ADR 0012)
    - documents: GET /orders/{number}/documents/ — dokumenty sprzedaży (ADR 0026)
    - return_options: GET /orders/{number}/return-options/ — formularz zwrotu
    - returns:  GET|POST /orders/{number}/returns/ — zgłoszenia zwrotu (#196)
    - return_detail: GET /orders/{number}/returns/{id}/ — jedno zgłoszenie

    Adresem jest numer zamówienia, nie identyfikator: to jego klient ma
    w wiadomości i to nim posługuje się w kontakcie ze sklepem. Gość
    dokłada do numeru swój adres e-mail — sam numer nie otwiera zamówienia.
    """

    permission_classes = [AllowAny]
    serializer_class = OrderSerializer
    lookup_field = "number"
    lookup_value_regex = "[A-Z0-9]+"
    filter_backends: list = []

    def get_queryset(self) -> QuerySet[Order]:
        items = OrderItem.objects.select_related("variant").order_by("created_at", "id")
        # Przesyłki dostają zamówienie z cache prefetchu, a metoda dostawy
        # przychodzi `select_related` — rodzaj metody nie dokłada zapytań.
        base = Order.objects.prefetch_related(
            Prefetch("items", queryset=items), "shipments"
        ).select_related("shipping_method")

        user = user_of(self.request)
        if user is not None:
            return base.for_subject(user=user)
        # Gość: lista nie istnieje, bo nie ma czego po niej filtrować poza
        # adresem, a ten sam w sobie nie jest dowodem tożsamości. Pojedyncze
        # zamówienie otwiera dopiero para numer + e-mail.
        email = self._guest_email()
        if self.action == "list" or not email:
            return base.none()
        return base.for_subject(email=email)

    def list(self, request: Request, *args, **kwargs) -> Response:
        if user_of(request) is None:
            raise NotAuthenticated(
                "Historia zamówień jest dostępna po zalogowaniu; gość otwiera "
                "pojedyncze zamówienie numerem i adresem e-mail."
            )
        return super().list(request, *args, **kwargs)

    def create(self, request: Request, *args, **kwargs) -> Response:
        payload = OrderCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data

        user = user_of(request)
        cart = get_cart(user=user, token=token_of(request))
        if cart is None:
            raise ValidationError(
                {"cart": "Nie ma koszyka, z którego dałoby się złożyć zamówienie."}
            )

        try:
            order = create_order(
                cart=cart,
                address=payload.to_address(),
                shipping_method=data["shipping_method"],
                user=user,
                email=data["email"],
                invoice_requested=data["invoice_requested"],
            )
        except DjangoValidationError as error:
            raise ValidationError(error.message_dict) from error

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def cancel(self, request: Request, *args, **kwargs) -> Response:
        """Anulowanie: `pending` od razu, `paid` przez zwrot u operatora.

        Opłacone w całości kuponem (bez płatności) anuluje się od razu.

        Opłacone zamówienie odpowiada 202 i zostaje `paid` — do `cancelled`
        przenosi je dopiero zdarzenie zwrotu (ADR 0012).
        """
        order = self.get_object()
        try:
            if order.status == OrderStatus.PAID and not is_covered_by_coupon(order):
                request_cancellation(order)
                order.refresh_from_db()
                return Response(
                    OrderSerializer(order).data, status=status.HTTP_202_ACCEPTED
                )
            cancel_order(order)
        except DjangoValidationError as error:
            raise ValidationError(error.message_dict) from error
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=["post"])
    def payment(self, request: Request, *args, **kwargs) -> Response:
        """Rozpoczęcie zapłaty — kolejne wywołanie to nowa próba."""
        order = self.get_object()
        try:
            started = start_payment(order)
        except DjangoValidationError as error:
            raise ValidationError(error.message_dict) from error
        return Response(
            PaymentIntentSerializer(started).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["get"], pagination_class=None)
    def documents(self, request: Request, *args, **kwargs) -> Response:
        """Dokumenty sprzedaży zamówienia z adresami podpisanymi na czas."""
        order = self.get_object()
        documents = order.documents.all()  # type: ignore[missing-attribute]
        return Response(SalesDocumentSerializer(documents, many=True).data)

    @action(
        detail=True, methods=["get"], url_path="return-options", pagination_class=None
    )
    def return_options(self, request: Request, *args, **kwargs) -> Response:
        """Co da się zwrócić, z jakiej podstawy i do kiedy."""
        order = self.get_object()
        options = build_return_options(order)
        return Response(ReturnOptionSerializer(options, many=True).data)

    @action(detail=True, methods=["get", "post"], pagination_class=None)
    def returns(self, request: Request, *args, **kwargs) -> Response:
        """Zgłoszenia zwrotu zamówienia; gość tą samą parą numer + e-mail."""
        order = self.get_object()
        if request.method == "GET":
            requests = order.return_requests.prefetch_related("items__order_item")  # type: ignore[missing-attribute]
            return Response(ReturnRequestSerializer(requests, many=True).data)

        payload = ReturnRequestCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        items = {item.pk: item for item in order.items.all()}  # type: ignore[missing-attribute]
        lines = []
        for line in data["items"]:
            item = items.get(line["order_item"])
            if item is None:
                raise ValidationError(
                    {"items": "Pozycja nie należy do tego zamówienia."}
                )
            lines.append(ReturnLine(item, line["quantity"], line["claim_request"]))
        try:
            created = create_return_request(order, reason=data["reason"], lines=lines)
        except DjangoValidationError as error:
            raise ValidationError(error.message_dict) from error
        return Response(
            ReturnRequestSerializer(created).data, status=status.HTTP_201_CREATED
        )

    @action(
        detail=True,
        methods=["get"],
        url_path=r"returns/(?P<id>[0-9a-f-]{36})",
        url_name="return-detail",
        pagination_class=None,
    )
    def return_detail(self, request: Request, *args, id: str, **kwargs) -> Response:
        """Jedno zgłoszenie — wyłącznie przez swoje zamówienie."""
        order = self.get_object()
        requests = order.return_requests.prefetch_related("items__order_item")  # type: ignore[missing-attribute]
        return Response(
            ReturnRequestSerializer(get_object_or_404(requests, pk=id)).data
        )

    def _guest_email(self) -> str:
        """E-mail gościa z parametru zapytania; pusty, gdy go nie podał."""
        lookup = OrderLookupSerializer(data=self.request.query_params)  # type: ignore[missing-attribute]
        if not lookup.is_valid():
            return ""
        return lookup.validated_data["email"]
