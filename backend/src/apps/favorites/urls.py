from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.favorites.views import FavoriteViewSet

router = DefaultRouter()
router.register(r"", FavoriteViewSet, basename="favorite")

urlpatterns = [
    path("", include(router.urls)),
]
