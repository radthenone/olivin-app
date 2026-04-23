from __future__ import annotations

import pytest

from tests.factories.accounts import AdminUserFactory, ProfileFactory, UserFactory


@pytest.fixture
def user_factory(db):
    """Fabryka użytkowników dostępna w testach accounts."""
    return UserFactory


@pytest.fixture
def admin_factory(db):
    """Fabryka adminów dostępna w testach accounts."""
    return AdminUserFactory


@pytest.fixture
def profile_factory(db):
    """Fabryka profili dostępna w testach accounts."""
    return ProfileFactory


@pytest.fixture
def user_with_profile(db):
    """Użytkownik z powiązanym profilem."""
    user = UserFactory()
    profile = ProfileFactory(user=user, first_name="Jan", last_name="Kowalski")
    return user, profile
