from __future__ import annotations

from factory.declarations import (  # noqa: F401 (reserved for future use)
    LazyAttribute,
    Sequence,
    SubFactory,
)
from factory.django import DjangoModelFactory
from factory.faker import Faker

from apps.accounts.models import CustomUser, Profile
from apps.accounts.models.roles_model import RoleChoices


class UserFactory(DjangoModelFactory):
    """Fabryka dla modelu CustomUser."""

    class Meta:
        model = CustomUser
        django_get_or_create = ("email",)

    email = Sequence(lambda n: f"user{n}@test.com")
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    is_active = True
    is_staff = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop("password", "testpass123!")
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, password=password, **kwargs)


class AdminUserFactory(UserFactory):
    """Fabryka dla superużytkownika."""

    is_staff = True
    is_superuser = True
    email = Sequence(lambda n: f"admin{n}@test.com")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop("password", "adminpass123!")
        manager = cls._get_manager(model_class)
        return manager.create_superuser(*args, password=password, **kwargs)


class ProfileFactory(DjangoModelFactory):
    """Fabryka dla modelu Profile."""

    class Meta:
        model = Profile

    user = SubFactory(UserFactory)
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    role = RoleChoices.CUSTOMER
