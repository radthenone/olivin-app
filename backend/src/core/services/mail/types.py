from __future__ import annotations

from typing import TypedDict


class EmailPayload(TypedDict):
    subject: str
    body: str
    from_email: str
    to: list[str]
    cc: list[str]
    bcc: list[str]
    reply_to: list[str]
    headers: dict[str, str]
    alternatives: dict[str, str]  # np. {"text/html": "<b>hi</b>"}
