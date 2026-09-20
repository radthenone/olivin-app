from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.products.models import (
    CostComponent,
    Gemstone,
    ProductImage,
    MetalRate,
    MetalRateStatus,
    Product,
    ProductStatus,
    ProductVariant,
)
from apps.products.pricing import calculate_price, cost_floor
from apps.products.services import activate_rate


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
        "margin_percent",
        "margin_amount",
        "vat_rate",
        "is_vat_exempt",
        "vat_exemption_basis",
    )
    show_change_link = True


class ProductImageInline(admin.TabularInline):
    """Zdjęcia przy produkcie — wgranie oryginału i kadr w jednym miejscu.

    Status i gotowe rozmiary są tylko do odczytu: powstają w zadaniu w tle,
    a wpisane ręcznie wskazywałyby pliki, których nie ma.
    """

    model = ProductImage
    extra = 1
    fields = (
        "original",
        "crop",
        "variant",
        "position",
        "is_primary",
        "alt_text",
        "status",
    )
    readonly_fields = ("status",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Panel katalogu — jedyne miejsce, w którym produkt powstaje (ADR 0021)."""

    inlines = [ProductVariantInline, ProductImageInline]
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


class GemstoneInline(admin.TabularInline):
    """Kamienie przy wariancie — parametry i certyfikat w jednym miejscu."""

    model = Gemstone
    extra = 1
    fields = (
        "kind",
        "carat",
        "clarity",
        "colour",
        "cut",
        "laboratory",
        "certificate_number",
        "certificate",
    )


class CostComponentInline(admin.TabularInline):
    """Składniki kosztu przy wariancie — lista otwarta (ADR 0022)."""

    model = CostComponent
    extra = 1
    fields = ("name", "amount", "currency")


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """Osobny ekran wariantu — potrzebny wyszukiwaniu po SKU i podglądowi ceny."""

    inlines = [CostComponentInline, GemstoneInline]
    list_display = ("sku", "product", "metal_color", "price", "manual_price")
    list_filter = ("metal_color", "stone", "is_vat_exempt")
    search_fields = ("sku", "product__name")
    ordering = ("sku",)
    autocomplete_fields = ("product",)
    readonly_fields = ("cost_floor_display", "calculated_price_display")

    def get_queryset(self, request: HttpRequest) -> QuerySet[ProductVariant]:
        return (
            super()
            .get_queryset(request)
            .select_related("product", "product__category")
            .prefetch_related("cost_components", "gemstones")
        )

    @admin.display(description="Próg kosztowy")
    def cost_floor_display(self, obj: ProductVariant) -> str:
        floor = cost_floor(obj) if obj.pk else None
        return str(floor) if floor is not None else "brak aktywnego kursu kruszcu"

    @admin.display(description="Cena ze wzoru")
    def calculated_price_display(self, obj: ProductVariant) -> str:
        price = calculate_price(obj) if obj.pk else None
        return str(price) if price is not None else "brak aktywnego kursu kruszcu"


@admin.register(MetalRate)
class MetalRateAdmin(admin.ModelAdmin):
    """Kursy kruszców. Aktywacja jest akcją, a nie zmianą pola.

    Powód: zatwierdzenie kursu przecenia cały katalog danego kruszcu, więc
    musi przejść przez jedną drogę, która archiwizuje poprzedni kurs, kolejkuje
    przeliczenie i wysyła wiadomość do właściciela.
    """

    list_display = (
        "metal",
        "fineness",
        "price_per_gram",
        "quoted_on",
        "status",
        "source",
        "activated_by",
    )
    list_filter = ("status", "metal", "fineness")
    search_fields = ("source",)
    ordering = ("-quoted_on",)
    actions = ("activate",)
    readonly_fields = ("status", "activated_at", "activated_by")
    fieldsets = (
        (None, {"fields": ("metal", "fineness", "price_per_gram", "currency")}),
        (None, {"fields": ("quoted_on", "source")}),
        (
            "Zatwierdzenie",
            {
                "fields": ("status", "activated_at", "activated_by"),
                "description": (
                    "Kurs aktywuje się akcją „Aktywuj” z listy. Poprzedni kurs "
                    "trafia do archiwum, ceny wariantów są przeliczane, "
                    "a właściciel dostaje wiadomość."
                ),
            },
        ),
    )

    @admin.action(description="Aktywuj zaznaczony kurs")
    def activate(self, request: HttpRequest, queryset: QuerySet[MetalRate]) -> None:
        # Jeden kurs naraz: aktywacja dwóch kursów tego samego kruszcu
        # w jednym kliknięciu nie ma sensownego wyniku, a właściciel i tak
        # musi zobaczyć, co zastąpił.
        rates = list(queryset[:2])
        if len(rates) != 1:
            self.message_user(
                request,
                "Zaznacz dokładnie jeden kurs do aktywacji.",
                messages.ERROR,
            )
            return

        rate = rates[0]
        if rate.status == MetalRateStatus.ARCHIVED:
            self.message_user(
                request,
                "Kurs zarchiwizowany nie wraca do obiegu — dodaj nowy.",
                messages.ERROR,
            )
            return

        result = activate_rate(rate, activated_by=request.user)
        previous = (
            f"Poprzedni kurs: {result.previous} za gram."
            if result.previous is not None
            else "To pierwszy kurs dla tej próby."
        )
        self.message_user(
            request,
            f"Aktywowano {rate}. {previous} Ceny wariantów są przeliczane.",
            messages.SUCCESS,
        )
