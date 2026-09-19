from __future__ import annotations

from django.http import Http404
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.categories.models import Category
from apps.categories.schema import category_schema
from apps.categories.serializers import CategorySerializer


@category_schema
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Drzewo kategorii dla menu sklepu.

    Actions:
    - list:     GET /categories/          — całe drzewo od korzeni
    - retrieve: GET /categories/{slug}/   — gałąź od wskazanego węzła

    Tylko odczyt: taksonomię układa właściciel w panelu, nie API (ADR 0021).
    """

    permission_classes = [AllowAny]
    serializer_class = CategorySerializer
    lookup_field = "slug"
    queryset = Category.objects.all()
    # Drzewo dzielone na strony przestaje być drzewem: gałąź trafiłaby na
    # stronę bez swojego korzenia. Taksonomia liczy dziesiątki węzłów.
    pagination_class = None

    def list(self, request: Request, *args, **kwargs) -> Response:
        categories = list(self.get_queryset())
        roots = [category for category in categories if category.parent_id is None]
        serializer = self.get_serializer(
            roots,
            many=True,
            context={
                **self.get_serializer_context(),
                **CategorySerializer.with_tree(categories),
            },
        )
        return Response(serializer.data)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        # Całe drzewo i tak jest potrzebne do złożenia potomków, więc szukany
        # węzeł bierzemy z już wczytanej listy zamiast dobijać bazę drugi raz.
        categories = list(self.get_queryset())
        slug = kwargs[self.lookup_field]
        category = next((node for node in categories if node.slug == slug), None)
        if category is None:
            raise Http404
        serializer = self.get_serializer(
            category,
            context={
                **self.get_serializer_context(),
                **CategorySerializer.with_tree(categories),
            },
        )
        return Response(serializer.data)
