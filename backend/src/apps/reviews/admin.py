from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.reviews.models import Review, ReviewStatus


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Moderacja opinii: akceptacja, odrzucenie albo usunięcie.

    Treść i ocenę wpisuje klient — panel decyduje wyłącznie o statusie
    (i o tym, czy opinia w ogóle zostaje).
    """

    list_display = ("product", "user", "rating", "status", "created_at")
    list_filter = ("status", "rating")
    search_fields = ("product__name", "user__username", "user__email", "comment")
    ordering = ("-created_at",)
    readonly_fields = (
        "product",
        "user",
        "rating",
        "comment",
        "created_at",
        "updated_at",
    )
    actions = ["approve", "reject"]

    @admin.action(description="Zaakceptuj opinie")
    def approve(self, request: HttpRequest, queryset: QuerySet[Review]) -> None:
        updated = queryset.update(status=ReviewStatus.APPROVED)
        self.message_user(request, f"Zaakceptowano opinii: {updated}.")

    @admin.action(description="Odrzuć opinie")
    def reject(self, request: HttpRequest, queryset: QuerySet[Review]) -> None:
        updated = queryset.update(status=ReviewStatus.REJECTED)
        self.message_user(request, f"Odrzucono opinii: {updated}.")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False
