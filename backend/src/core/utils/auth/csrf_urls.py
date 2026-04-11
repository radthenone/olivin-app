from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .csrf_views import CsrfViewSet

router = DefaultRouter()

router.register("", CsrfViewSet, basename="csrf")

urlpatterns = [
    path("", include(router.urls)),
]
