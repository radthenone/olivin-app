from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.products.models import Product, ProductStatus, ProductVariant


class ProductVariantInline(admin.TabularInline):
    """Warianty edytowane przy produkcie — osobny ekran rozbiłby jedną pracę."""

    model = ProductVariant
    extra = 1
    fields = (
        "sku",
        "metal_color",
        "size",
        "length",
        "stone",
        "metal_weight_grams",
        "price",
        "manual_price",
        "currency",
        "vat_rate",
        "is_vat_exempt",
        "vat_exemption_basis",
    )
    show_change_link = True


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Panel katalogu — jedyne miejsce, w którym produkt powstaje (ADR 0021)."""

    inlines = [ProductVariantInline]
    list_display = ("name", "category", "material", "fineness", "status")
    list_filter = ("status", "material", "fineness", "is_made_to_order", "category")
    search_fields = ("name", "slug", "variants__sku")
    ordering = ("-created_at",)
    autocomplete_fields = ("category",)
    actions = ("publish", "unpublish")
    fieldsets = (
        (None, {"fields": ("name", "slug", "description", "category")}),
        ("Kruszec", {"fields": ("material", "fineness")}),
        (
            "Publikacja",
            {
                "fields": ("status",),
                "description": (
                    "Szkic nie jest widoczny w sklepie pod żadnym adresem. "
                    "Po publikacji slug jest zablokowany."
                ),
            },
        ),
        (
            "Produkt na zamówienie",
            {
                "fields": ("is_made_to_order", "production_time_days"),
                "description": (
                    "Wyrób wytwarzany po złożeniu zamówienia nie ma stanu "
                    "magazynowego, ma za to czas realizacji (ADR 0024)."
                ),
            },
        ),
    )

    def get_readonly_fields(
        self, request: HttpRequest, obj: Product | None = None
    ) -> tuple[str, ...]:
        # Slug zamraża się dopiero przy publikacji — szkic wolno jeszcze
        # poprawiać, bo nikt nie wszedł jeszcze pod ten adres.
        return ("slug",) if obj is not None and obj.is_published else ()

    def get_queryset(self, request: HttpRequest) -> QuerySet[Product]:
        return super().get_queryset(request).select_related("category")

    @admin.action(description="Opublikuj zaznaczone produkty")
    def publish(self, request: HttpRequest, queryset: QuerySet[Product]) -> None:
        self._set_status(request, queryset, ProductStatus.PUBLISHED)

    @admin.action(description="Cofnij do szkicu")
    def unpublish(self, request: HttpRequest, queryset: QuerySet[Product]) -> None:
        self._set_status(request, queryset, ProductStatus.DRAFT)

    def _set_status(
        self,
        request: HttpRequest,
        queryset: QuerySet[Product],
        status: str,
    ) -> None:
        # Po jednym `save()`, a nie zbiorczym `update()`: to zapis modelu
        # pilnuje niezmienności sluga i spójności czasu realizacji.
        changed = 0
        for product in queryset:
            if product.status == status:
                continue
            product.status = status
            product.save(update_fields=["status", "updated_at"])
            changed += 1
        self.message_user(
            request,
            f"Zmieniono status {changed} produktów.",
            messages.SUCCESS,
        )


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """Osobny ekran wariantu — potrzebny wyszukiwaniu po SKU i podglądowi ceny."""

    list_display = ("sku", "product", "metal_color", "price", "manual_price")
    list_filter = ("metal_color", "stone", "is_vat_exempt")
    search_fields = ("sku", "product__name")
    ordering = ("sku",)
    autocomplete_fields = ("product",)
