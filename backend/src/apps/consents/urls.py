from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.consents.views import ConsentDocumentViewSet, ConsentViewSet

router = DefaultRouter()
router.register(r"documents", ConsentDocumentViewSet, basename="consent-document")
router.register(r"", ConsentViewSet, basename="consent")

urlpatterns = [
    path("", include(router.urls)),
]
