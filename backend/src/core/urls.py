"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from allauth.headless.constants import Client

from core.utils import (
    AllauthRedocView,
    AllauthSwaggerView,
    ConfirmLoginCodeView,
    HealthCheckView,
    RequestLoginCodeView,
)

HEADLESS_CLIENTS = (Client.APP, Client.BROWSER)
LOGIN_CODE_VIEWS = (
    ("request", RequestLoginCodeView),
    ("confirm", ConfirmLoginCodeView),
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    path("health/", HealthCheckView.as_view(), name="health_check"),
    # API
    path("customers/", include("apps.accounts.urls")),
    path("cart/", include("apps.orders.urls")),
    path("categories/", include("apps.categories.urls")),
    path("orders/", include("apps.orders.order_urls")),
    path("collections/", include("apps.collections.urls")),
    path("consents/", include("apps.consents.urls")),
    path("favorites/", include("apps.favorites.urls")),
    path("watches/", include("apps.watches.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("payments/", include("apps.payments.urls")),
    path("products/", include("apps.products.urls")),
    path("promotions/", include("apps.promotions.urls")),
    path("reviews/", include("apps.reviews.urls")),
    path("shipping-methods/", include("apps.shipping.urls")),
    # Headless API
    path("accounts/", include("allauth.urls")),
    # Logowanie kodem: własne widoki, żeby limit zwracał 429 zamiast 400 (#407).
    *[
        path(
            f"_allauth/{client.value}/v1/auth/code/{suffix}",
            view.as_api_view(client=client),
        )
        for client in HEADLESS_CLIENTS
        for suffix, view in LOGIN_CODE_VIEWS
    ],
    path("_allauth/", include("allauth.headless.urls")),
]

if settings.DEBUG:
    urlpatterns += [
        path("csrf/", include("core.utils.auth.csrf_urls")),
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            "api/docs/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
        path(
            "api/redoc/",
            SpectacularRedocView.as_view(url_name="schema"),
            name="redoc",
        ),
        path(
            "_allauth/docs/",
            AllauthSwaggerView.as_view(),
            name="allauth-swagger",
        ),
        path(
            "_allauth/redoc/",
            AllauthRedocView.as_view(),
            name="allauth-redoc",
        ),
    ]
    if "silk" in settings.INSTALLED_APPS:
        urlpatterns += [path("silk/", include("silk.urls", namespace="silk"))]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        from debug_toolbar.toolbar import debug_toolbar_urls

        urlpatterns += debug_toolbar_urls()
