"""Panel promocji: akcja „ogłoś promocję” bez podwójnego ogłoszenia (#203)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.urls import reverse

from tests.factories.promotions import PromotionFactory

TASK = "apps.notifications.tasks.announce_promotion"


def _announce_via_admin(admin_client, *promotions) -> None:
    admin_client.post(
        reverse("admin:promotions_promotion_changelist"),
        {
            "action": "announce",
            "_selected_action": [str(promotion.pk) for promotion in promotions],
        },
    )


@pytest.mark.django_db(transaction=True)
class TestAnnounceAction:
    """Akcja panelu ogłaszająca promocję."""

    def test_queues_announcement_and_marks_promotion(self, admin_client):
        """Akcja kolejkuje ogłoszenie i oznacza promocję."""
        promotion = PromotionFactory()

        with patch(TASK) as task:
            _announce_via_admin(admin_client, promotion)

        task.delay.assert_called_once_with(promotion_id=str(promotion.pk))
        promotion.refresh_from_db()
        assert promotion.announced_at is not None

    def test_second_announcement_of_same_promotion_is_skipped(self, admin_client):
        """Drugie ogłoszenie tej samej promocji jest pomijane."""
        promotion = PromotionFactory()

        with patch(TASK) as task:
            _announce_via_admin(admin_client, promotion)
            _announce_via_admin(admin_client, promotion)

        task.delay.assert_called_once()

    def test_mixed_selection_announces_only_new_ones(self, admin_client):
        """Z mieszanego zaznaczenia ogłaszane są tylko nowe promocje."""
        announced = PromotionFactory()
        fresh = PromotionFactory()
        with patch(TASK):
            _announce_via_admin(admin_client, announced)

        with patch(TASK) as task:
            _announce_via_admin(admin_client, announced, fresh)

        task.delay.assert_called_once_with(promotion_id=str(fresh.pk))

    def test_failed_queueing_releases_announcement_for_retry(self, admin_client):
        """Broker niedostępny: promocja nie może zostać „ogłoszona” bez wysyłki."""
        promotion = PromotionFactory()

        with patch(TASK) as task:
            task.delay.side_effect = ConnectionError("broker down")
            _announce_via_admin(admin_client, promotion)

        promotion.refresh_from_db()
        assert promotion.announced_at is None

    def test_reset_action_allows_announcing_again(self, admin_client):
        """Akcja resetu pozwala ogłosić promocję ponownie."""
        promotion = PromotionFactory()
        with patch(TASK):
            _announce_via_admin(admin_client, promotion)

        admin_client.post(
            reverse("admin:promotions_promotion_changelist"),
            {"action": "reset_announcement", "_selected_action": [str(promotion.pk)]},
        )
        with patch(TASK) as task:
            _announce_via_admin(admin_client, promotion)

        task.delay.assert_called_once_with(promotion_id=str(promotion.pk))
