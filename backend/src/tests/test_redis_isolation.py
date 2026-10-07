"""Testy nie podmieniają globalnie klas klienta Redis."""

from __future__ import annotations

import redis


def test_redis_client_classes_are_real_types():
    """`redis.Redis` to klasa, nie atrapa — `kombu.transport.redis` może po niej dziedziczyć."""
    assert isinstance(redis.Redis, type)
    assert isinstance(redis.StrictRedis, type)


def test_kombu_redis_transport_imports():
    """Import transportu Redis w trakcie testu nie pada na `metaclass conflict`."""
    import importlib
    import sys

    sys.modules.pop("kombu.transport.redis", None)
    module = importlib.import_module("kombu.transport.redis")

    assert issubclass(module.PrefixedStrictRedis, redis.Redis)
