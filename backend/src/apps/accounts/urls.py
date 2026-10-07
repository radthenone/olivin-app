from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.views import (
    AccountAnonymiseCodeView,
    AccountAnonymiseView,
    AddressViewSet,
    ProfileViewSet,
)

router = DefaultRouter()
router.register(r"addresses", AddressViewSet, basename="address")
router.register(r"profile", ProfileViewSet, basename="profile")

urlpatterns = [
    path(
        "account/anonymise/",
        AccountAnonymiseView.as_view(),
        name="account-anonymise",
    ),
    path(
        "account/anonymise/code/",
        AccountAnonymiseCodeView.as_view(),
        name="account-anonymise-code",
    ),
    path("", include(router.urls)),
]
