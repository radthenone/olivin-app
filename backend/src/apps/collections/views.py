from __future__ import annotations

from django.db.models import Count, Q, QuerySet
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.collections.models import Collection
from apps.collections.schema import collection_schema
from apps.collections.serializers import CollectionSerializer
from apps.products.models import ProductStatus

PRODUCT_COUNT = "product_count"


@collection_schema
class CollectionViewSet(viewsets.ReadOnlyModelViewSet):
    """Kolekcje marketingowe sklepu.

    Actions:
    - list:     GET /collections/         — kolekcje z opublikowanymi produktami
    - retrieve: GET /collections/{slug}/  — pojedyncza kolekcja

    Tylko odczyt: kolekcje układa właściciel w panelu, nie API (ADR 0021).
    Kolekcja, w której nie ma ani jednego opublikowanego produktu, nie pojawia
    się nigdzie — pusta kampania to dla odwiedzającego ślepy zaułek, a szkice
    nie istnieją dla sklepu pod żadnym adresem.
    """

    permission_classes = [AllowAny]
    serializer_class = CollectionSerializer
    lookup_field = "slug"

    def get_queryset(self) -> QuerySet[Collection]:
        published = Q(products__status=ProductStatus.PUBLISHED)
        return (
            Collection.objects.annotate(
                **{PRODUCT_COUNT: Count("products", filter=published, distinct=True)}
            )
            .filter(**{f"{PRODUCT_COUNT}__gt": 0})
            .prefetch_related("translations")
            .order_by("name", "id")
        )
