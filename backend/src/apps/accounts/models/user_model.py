from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from accounts.managers import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Model użytkownika z emailem jako głównym identyfikatorem.
    Username jest opcjonalne i unikalne (NULL nie łamie UNIQUE w PostgreSQL)."""

    email = models.EmailField(unique=True, verbose_name="adres e-mail")
    username = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        unique=True,
        verbose_name="nazwa użytkownika",
    )
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Użytkownik"
        verbose_name_plural = "Użytkownicy"

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
