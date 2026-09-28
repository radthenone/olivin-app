from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.notifications.views import (
    NotificationPreferenceView,
    NotificationViewSet,
    PushDeviceViewSet,
)

router = DefaultRouter()
router.register(r"", NotificationViewSet, basename="notification")
router.register(r"devices", PushDeviceViewSet, basename="push-device")

urlpatterns = [
    path(
        "preferences/",
        NotificationPreferenceView.as_view(),
        name="notification-preferences",
    ),
    path("", include(router.urls)),
]
