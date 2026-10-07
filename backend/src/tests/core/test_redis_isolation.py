"""Testy nie podmieniają globalnie klas klienta Redis."""

from __future__ import annotations

import importlib
import sys

import pytest
import redis

pytestmark = pytest.mark.unit


def test_redis_client_classes_are_real_types():
    """`redis.Redis` to klasa, nie atrapa — `kombu.transport.redis` może po niej dziedziczyć."""
    assert isinstance(redis.Redis, type)
    assert isinstance(redis.StrictRedis, type)


def test_kombu_redis_transport_imports(monkeypatch):
    """Import transportu Redis w trakcie testu nie pada na `metaclass conflict`."""
    monkeypatch.delitem(sys.modules, "kombu.transport.redis", raising=False)

    module = importlib.import_module("kombu.transport.redis")

    assert issubclass(module.PrefixedStrictRedis, redis.Redis)
