from datetime import date

from django.db import IntegrityError, transaction
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from apps.accounts.models import CustomUser, Profile
from apps.accounts.usernames import (
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
    is_reserved_username,
    username_chars_validator,
)

USERNAME_TAKEN = "Ta nazwa użytkownika jest już zajęta."


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    # Publiczna nazwa klienta (#195); zmiana przez PATCH profilu.
    username = serializers.CharField(
        source="user.username",
        required=False,
        min_length=USERNAME_MIN_LENGTH,
        max_length=USERNAME_MAX_LENGTH,
        validators=[username_chars_validator],
    )
    phone_number = PhoneNumberField(required=False, allow_blank=True)
    full_name = serializers.SerializerMethodField(read_only=True)
    age = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "age",
            "phone_number",
            "role",
        ]
        read_only_fields = ["id", "email", "role"]

    def get_full_name(self, obj: Profile) -> str:
        return obj.full_name

    def get_age(self, obj: Profile) -> int | None:
        return obj.age

    def _owner(self) -> CustomUser | None:
        """Konto, którego nazwę zmieniamy: z profilu albo (przy POST) z requestu."""
        if self.instance is not None:
            return self.instance.user
        user = getattr(self.context.get("request"), "user", None)
        return user if isinstance(user, CustomUser) else None

    def validate_username(self, value: str) -> str:
        """Nazwa dozwolona i unikalna bez względu na wielkość liter.

        Odesłanie bieżącej nazwy (także `anon…`) bez zmian jest poprawne.
        """
        owner = self._owner()
        if owner is not None and owner.username == value:
            return value
        if is_reserved_username(value):
            raise serializers.ValidationError("Ta nazwa użytkownika jest zastrzeżona.")
        taken = CustomUser.objects.filter(username__iexact=value)
        if owner is not None:
            taken = taken.exclude(pk=owner.pk)
        if taken.exists():
            raise serializers.ValidationError(USERNAME_TAKEN)
        return value

    @staticmethod
    def _save_username(user: CustomUser, username: str) -> None:
        """Zapisuje nazwę; duplikat z wyścigu (IntegrityError) → 400, nie 500."""
        user.username = username
        try:
            with transaction.atomic():
                user.save(update_fields=["username"])
        except IntegrityError as exc:
            raise serializers.ValidationError({"username": [USERNAME_TAKEN]}) from exc

    def create(self, validated_data: dict) -> Profile:
        """Tworzy profil; `username` z body zapisuje na koncie właściciela.

        `save(user=...)` w widoku nadpisuje zagnieżdżone `user`, więc nazwę
        bierzemy z `self.validated_data`.
        """
        user_data = self.validated_data.get("user")
        with transaction.atomic():
            profile = super().create(validated_data)
            if isinstance(user_data, dict) and "username" in user_data:
                self._save_username(profile.user, user_data["username"])
        return profile

    def update(self, instance: Profile, validated_data: dict) -> Profile:
        """Zapisuje nazwę na koncie (`user.username`), resztę na profilu — atomowo."""
        user_data = validated_data.pop("user", {})
        with transaction.atomic():
            profile = super().update(instance, validated_data)
            if "username" in user_data:
                self._save_username(instance.user, user_data["username"])
        return profile

    def validate_date_of_birth(self, value: date | None) -> date | None:
        """Waliduje, że klient ma ukończone 18 lat."""
        if value is None:
            return value

        today = date.today()

        try:
            adult_birth_date = today.replace(year=today.year - 18)
        except ValueError:
            adult_birth_date = today.replace(year=today.year - 18, day=28)

        if value > adult_birth_date:
            raise serializers.ValidationError("Użytkownik musi mieć ukończone 18 lat.")

        return value
