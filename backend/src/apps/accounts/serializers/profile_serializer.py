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
            "email",
            "first_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "age",
            "phone_number",
            "role",
        ]
        read_only_fields = ["email", "role"]

    def get_full_name(self, obj: Profile) -> str:
        return obj.full_name

    def get_age(self, obj: Profile) -> int | None:
        return obj.age