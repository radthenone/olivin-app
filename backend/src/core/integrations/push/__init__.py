"""Adapter push dla powiadomień (ADR 0027)."""

from core.integrations.push.base import PushProviderError
from core.integrations.push.registry import get_provider

__all__ = ["PushProviderError", "get_provider"]
