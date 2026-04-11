from __future__ import annotations

from django.core.mail import EmailMultiAlternatives

from .types import EmailPayload


class MailService:
    @staticmethod
    def serialize(message) -> EmailPayload:
        alternatives: dict[str, str] = {}
        for content, mimetype in getattr(message, "alternatives", []) or []:
            alternatives[mimetype] = content

        return {
            "subject": str(getattr(message, "subject", "")),
            "body": str(getattr(message, "body", "")),
            "from_email": str(getattr(message, "from_email", "")),
            "to": list(getattr(message, "to", []) or []),
            "cc": list(getattr(message, "cc", []) or []),
            "bcc": list(getattr(message, "bcc", []) or []),
            "reply_to": list(getattr(message, "reply_to", []) or []),
            "headers": dict(getattr(message, "extra_headers", {}) or {}),
            "alternatives": alternatives,
        }

    @staticmethod
    def build(payload: EmailPayload, *, connection) -> EmailMultiAlternatives:
        msg = EmailMultiAlternatives(
            subject=payload["subject"],
            body=payload["body"],
            from_email=payload["from_email"],
            to=payload["to"],
            cc=payload["cc"],
            bcc=payload["bcc"],
            reply_to=payload["reply_to"],
            headers=payload["headers"],
            connection=connection,
        )

        html = payload.get("alternatives", {}).get("text/html")
        if html:
            msg.attach_alternative(html, "text/html")

        return msg
