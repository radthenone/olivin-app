from django.urls import include, path
from rest_framework.routers import SimpleRouter

from apps.orders.views import (
    CartDetailView,
    CartItemViewSet,
    CartMergeView,
    CartPromotionCodeView,
)

# `SimpleRouter`, nie `DefaultRouter`: korzeń `/cart/` należy do widoku
# koszyka, więc api-root generowany przez ten drugi i tak byłby przykryty.
router = SimpleRouter()
router.register(r"items", CartItemViewSet, basename="cart-item")

urlpatterns = [
    path("", CartDetailView.as_view(), name="cart-detail"),
    path("merge/", CartMergeView.as_view(), name="cart-merge"),
    path(
        "promotion-code/",
        CartPromotionCodeView.as_view(),
        name="cart-promotion-code",
    ),
    path("", include(router.urls)),
]
