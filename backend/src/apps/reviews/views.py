from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.reviews.models import Review
from apps.reviews.schema import review_schema
from apps.reviews.serializers import (
    MyReviewSerializer,
    ProductToReviewSerializer,
    ReviewCreateSerializer,
    ReviewUpdateSerializer,
)
from apps.reviews.services import create_review, products_to_review, update_review


def _as_drf_error(error: DjangoValidationError) -> ValidationError:
    if hasattr(error, "message_dict"):
        return ValidationError(error.message_dict)
    return ValidationError(error.messages)


@review_schema
class ReviewViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """Opinie klienta o kupionych produktach.

    Actions:
    - list:           GET   /reviews/            — własne opinie, każdy status
    - create:         POST  /reviews/             — nowa opinia
    - partial_update: PATCH /reviews/{id}/        — edycja wraca do moderacji
    - to_review:      GET   /reviews/to-review/   — dostarczone produkty bez opinii

    Publiczna lista opinii produktu żyje osobno, jako akcja `ProductViewSet`
    (`GET /products/{slug}/reviews/`) — tam nie trzeba logowania.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = MyReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user).select_related("product")

    def create(self, request: Request, *args, **kwargs) -> Response:
        payload = ReviewCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            review = create_review(user=request.user, **payload.validated_data)
        except DjangoValidationError as error:
            raise _as_drf_error(error) from error
        return Response(MyReviewSerializer(review).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request: Request, *args, **kwargs) -> Response:
        review = self.get_object()
        payload = ReviewUpdateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            review = update_review(review, **payload.validated_data)
        except DjangoValidationError as error:
            raise _as_drf_error(error) from error
        return Response(MyReviewSerializer(review).data)

    @action(detail=False, methods=["get"], url_path="to-review", pagination_class=None)
    def to_review(self, request: Request, *args, **kwargs) -> Response:
        """Produkty z dostarczonych zamówień, których klient jeszcze nie ocenił."""
        products = products_to_review(request.user)
        return Response(ProductToReviewSerializer(products, many=True).data)
