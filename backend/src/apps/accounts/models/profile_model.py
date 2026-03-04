from datetime import date

from django.conf import settings
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from apps.accounts.models.roles_model import RoleChoices
from common import TimestampedModel

# Create your models here.

class Profile(TimestampedModel):
    """User profile model storing additional user information.

    Attributes:
        user: One-to-one relationship with the User model.
        first_name: User's first name.
        last_name: User's last name.
        date_of_birth: User's date of birth.
        phone_number: Primary phone number with country code.
        role: User's role in the system.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        )
    first_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="User's first name",
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="User's last name",
    )
    date_of_birth = models.DateField(
        null=True, blank=True, help_text="User's date of birth"
    )
    phone_number = PhoneNumberField(
        blank=True,
        help_text="Primary phone number with country code",
        )
    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.CUSTOMER,
        )

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.role}"

    @property
    def full_name(self):
        """Returns the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def age(self):
        """Calculates the user's age based on their date of birth."""
        if self.date_of_birth:
            today = date.today()
            return (
                today.year
                - self.date_of_birth.year
                - (
                    (today.month, today.day)
                    < (self.date_of_birth.month, self.date_of_birth.day)
                )
            )
        return None