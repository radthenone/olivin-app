from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.shipping.views import ShippingMethodViewSet

router = DefaultRouter()
router.register(r"", ShippingMethodViewSet, basename="shipping-method")

urlpatterns = [
    path("", include(router.urls)),
]
