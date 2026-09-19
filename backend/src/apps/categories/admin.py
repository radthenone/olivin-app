from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.categories.models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Panel taksonomii — jedyne miejsce, w którym drzewo się zmienia (ADR 0021)."""

    list_display = ("name", "path", "slug", "margin_display")
    list_filter = ("parent",)
    search_fields = ("name", "slug")
    ordering = ("name",)
    autocomplete_fields = ("parent",)
    fieldsets = (
        (None, {"fields": ("name", "slug", "parent")}),
        (
            "Narzut domyślny",
            {
                "fields": ("margin_percent", "margin_amount"),
                "description": (
                    "Narzut jest procentowy albo kwotowy — nie oba naraz. "
                    "Warianty dziedziczą go z kategorii (ADR 0022)."
                ),
            },
        ),
    )

    def get_readonly_fields(
        self, request: HttpRequest, obj: Category | None = None
    ) -> tuple[str, ...]:
        # Slug jest niezmienny po zapisie; model i tak to odrzuci, ale pole
        # wyszarzone tłumaczy to zanim właściciel zobaczy błąd walidacji.
        return ("slug",) if obj is not None else ()

    def get_queryset(self, request: HttpRequest) -> QuerySet[Category]:
        # Dwa poziomy w przód wystarczają na ścieżkę typowej taksonomii;
        # głębsze drzewo dobije bazę tylko o brakujące węzły.
        return super().get_queryset(request).select_related("parent__parent")

    @admin.display(description="Ścieżka")
    def path(self, obj: Category) -> str:
        # Zbiór odwiedzonych, bo panel ma pokazać uszkodzone dane, a nie
        # zawiesić się na nich: zapis pętli nie przepuszcza, ale rekord
        # zmieniony z pominięciem modelu nadal może ją zawierać.
        names = [obj.name]
        seen = {obj.pk}
        node = obj.parent
        while node is not None and node.pk not in seen:
            names.append(node.name)
            seen.add(node.pk)
            node = node.parent
        return " → ".join(reversed(names))

    @admin.display(description="Narzut")
    def margin_display(self, obj: Category) -> str:
        if obj.margin_percent is not None:
            return f"{obj.margin_percent}%"
        margin = obj.margin
        return str(margin) if margin is not None else "—"
