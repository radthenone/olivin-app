from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.collections.models import Collection


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    """Panel kolekcji — jedyne miejsce, w którym powstają (ADR 0021)."""

    list_display = ("name", "slug", "product_count")
    search_fields = ("name", "slug")
    ordering = ("name",)
    # Produktów będą setki, więc zwykły widget wielokrotnego wyboru byłby
    # listą nie do przewinięcia; `filter_horizontal` daje wyszukiwanie po
    # obu stronach przypisania.
    filter_horizontal = ("products",)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Collection]:
        return super().get_queryset(request).prefetch_related("products")

    @admin.display(description="Produkty")
    def product_count(self, obj: Collection) -> int:
        return obj.products.count()
