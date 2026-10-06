from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.watches.views import WatchViewSet

router = DefaultRouter()
router.register(r"", WatchViewSet, basename="watch")

urlpatterns = [
    path("", include(router.urls)),
]
