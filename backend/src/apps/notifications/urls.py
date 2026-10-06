from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.notifications.views import (
    NewsletterConfirmView,
    NewsletterSubscribeView,
    NewsletterUnsubscribeView,
    NotificationPreferenceView,
    NotificationViewSet,
    PushDeviceViewSet,
)

router = DefaultRouter()
router.register(r"", NotificationViewSet, basename="notification")
router.register(r"devices", PushDeviceViewSet, basename="push-device")

urlpatterns = [
    path(
        "newsletter/subscribe/",
        NewsletterSubscribeView.as_view(),
        name="newsletter-subscribe",
    ),
    path(
        "newsletter/confirm/",
        NewsletterConfirmView.as_view(),
        name="newsletter-confirm",
    ),
    path(
        "newsletter/unsubscribe/",
        NewsletterUnsubscribeView.as_view(),
        name="newsletter-unsubscribe",
    ),
    path(
        "preferences/",
        NotificationPreferenceView.as_view(),
        name="notification-preferences",
    ),
    path("", include(router.urls)),
]
