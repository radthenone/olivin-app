from django_countries.serializers import CountryFieldMixin
from rest_framework import serializers

from apps.accounts.models import Address


class AddressSerializer(CountryFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id",
            "street",
            "street2",
            "city",
            "state",
            "postal_code",
            "country",
            "is_default",
        ]