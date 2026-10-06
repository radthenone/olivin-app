"""Panel obserwowanych: podgląd bez edycji, usunięcie zostaje (#201)."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.watches.models import Watch
from tests.factories.watches import WatchFactory


@pytest.mark.django_db
class TestWatchAdmin:
    """Panel pokazuje wpisy, ale nie pozwala ich zakładać ani edytować."""

    def test_changelist_loads(self, admin_client):
        WatchFactory()

        response = admin_client.get(reverse("admin:watches_watch_changelist"))

        assert response.status_code == 200

    def test_add_view_is_forbidden(self, admin_client):
        response = admin_client.get(reverse("admin:watches_watch_add"))

        assert response.status_code == 403

    def test_delete_removes_watch(self, admin_client):
        watch = WatchFactory()

        admin_client.post(
            reverse("admin:watches_watch_changelist"),
            {
                "action": "delete_selected",
                "_selected_action": [str(watch.pk)],
                "post": "yes",
            },
        )

        assert not Watch.objects.filter(pk=watch.pk).exists()
