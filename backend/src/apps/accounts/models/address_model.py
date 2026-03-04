from django.db import models
from django_countries.fields import CountryField

from common import TimestampedModel


class Address(TimestampedModel):
    """User address model storing user's address information.

    Attributes:
        profile: Foreign key to the Profile model.
        street: Street address.
        city: City name.
        state: State or province name.
        postal_code: Postal or ZIP code.
        country: Country name.
        is_default: Indicates if this is the default address for the profile.
    """
    profile = models.ForeignKey(
        "Profile",
        on_delete=models.CASCADE,
        related_name="addresses",
        help_text="Profile associated with this address",
    )
    street = models.CharField(max_length=255, blank=True, help_text="Street address")
    street2 = models.CharField(max_length=255, blank=True, help_text="Street address line 2")
    city = models.CharField(max_length=100, blank=True, help_text="City name")
    state = models.CharField(max_length=100, blank=True, help_text="State or province name")
    postal_code = models.CharField(max_length=20, blank=True, help_text="Postal or ZIP code")
    country = CountryField(blank=True, help_text="Country name")
    is_default = models.BooleanField(default=False, help_text="Is this the default address?")


    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.street}, {self.city}, {self.state}, {self.postal_code}, {self.country}"