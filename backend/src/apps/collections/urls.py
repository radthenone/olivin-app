from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.collections.views import CollectionViewSet

router = DefaultRouter()
router.register(r"", CollectionViewSet, basename="collection")

urlpatterns = [
    path("", include(router.urls)),
]
