"""Adapter e-mail bez atrap — trafia do `mail.outbox` (#156, review)."""

from __future__ import annotations

import pytest

from core.integrations.notifications.mail import send_notification_email


@pytest.mark.django_db
def test_send_notification_email_lands_in_outbox(mailoutbox):
    send_notification_email(
        to="klient@test.com", subject="Temat", body="Treść wiadomości"
    )

    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.to == ["klient@test.com"]
    assert message.subject == "Temat"
    assert message.body == "Treść wiadomości"
