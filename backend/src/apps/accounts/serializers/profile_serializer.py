from datetime import date

from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from apps.accounts.models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    phone_number = PhoneNumberField(required=False, allow_blank=True)
    full_name = serializers.SerializerMethodField(read_only=True)
    age = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "email",
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
