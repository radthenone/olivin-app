from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.views import AddressViewSet, ProfileViewSet

router = DefaultRouter()
router.register(r"addresses", AddressViewSet, basename="address")
router.register(r"profile", ProfileViewSet, basename="profile")

urlpatterns = [
    path("", include(router.urls)),
]
