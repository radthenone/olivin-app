"""Panel ulubionych: podgląd bez edycji, usunięcie zostaje (#200)."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.favorites.models import Favorite
from tests.factories.favorites import FavoriteFactory


@pytest.mark.django_db
class TestFavoriteAdmin:
    """Panel pokazuje wpisy, ale nie pozwala ich zakładać ani edytować."""

    def test_changelist_loads(self, admin_client):
        """Lista wpisów w panelu się otwiera."""
        FavoriteFactory()

        response = admin_client.get(reverse("admin:favorites_favorite_changelist"))

        assert response.status_code == 200

    def test_add_view_is_forbidden(self, admin_client):
        """Dodawanie wpisów w panelu jest zabronione."""
        response = admin_client.get(reverse("admin:favorites_favorite_add"))

        assert response.status_code == 403

    def test_change_view_is_read_only(self, admin_client):
        """Bez uprawnienia do zmiany Django pokazuje formularz w trybie
        tylko-do-odczytu (200), zamiast zabraniać podglądu (403)."""
        favorite = FavoriteFactory()

        response = admin_client.get(
            reverse("admin:favorites_favorite_change", args=[favorite.pk])
        )

        assert response.status_code == 200
        assert response.context["adminform"].form.fields == {}

    def test_delete_removes_favorite(self, admin_client):
        """Usunięcie w panelu kasuje wpis."""
        favorite = FavoriteFactory()

        admin_client.post(
            reverse("admin:favorites_favorite_changelist"),
            {
                "action": "delete_selected",
                "_selected_action": [str(favorite.pk)],
                "post": "yes",
            },
        )

        assert not Favorite.objects.filter(pk=favorite.pk).exists()
