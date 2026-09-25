from datetime import date

from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from apps.accounts.models import CustomUser, Profile
from apps.accounts.usernames import (
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
    username_chars_validator,
)


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

    def validate_username(self, value: str) -> str:
        """Nazwa unikalna bez względu na wielkość liter; własna obecna jest OK."""
        taken = CustomUser.objects.filter(username__iexact=value)
        if self.instance is not None:
            taken = taken.exclude(pk=self.instance.user_id)
        if taken.exists():
            raise serializers.ValidationError("Ta nazwa użytkownika jest już zajęta.")
        return value

    def update(self, instance: Profile, validated_data: dict) -> Profile:
        """Zapisuje nazwę na koncie (`user.username`), resztę na profilu."""
        user_data = validated_data.pop("user", {})
        if "username" in user_data:
            instance.user.username = user_data["username"]
            instance.user.save(update_fields=["username"])
        return super().update(instance, validated_data)

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
