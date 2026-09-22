from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.orders.views import CartDetailView, CartItemViewSet, CartMergeView

router = DefaultRouter()
router.register(r"items", CartItemViewSet, basename="cart-item")

urlpatterns = [
    path("", CartDetailView.as_view(), name="cart-detail"),
    path("merge/", CartMergeView.as_view(), name="cart-merge"),
    path("", include(router.urls)),
]
