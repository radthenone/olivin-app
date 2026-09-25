from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import IntegrityError, models, transaction
from django.db.models import Q

from apps.accounts.managers import CustomUserManager
from apps.accounts.usernames import ANON_USERNAME_MAX_ATTEMPTS, generate_anon_username


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Model użytkownika z emailem jako głównym identyfikatorem.
    Username zawsze niepuste i unikalne — gdy klient go nie wybrał, zapis nadaje
    `anon<liczba>` (#195). Logowanie nadal wyłącznie e-mailem."""

    email = models.EmailField(unique=True, verbose_name="adres e-mail")
    # blank=True: formularze (admin, allauth) mogą zostawić puste — nazwę nadaje save().
    username = models.CharField(
        max_length=150,
        blank=True,
        unique=True,
        verbose_name="nazwa użytkownika",
    )
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    # Menedżer na modelu użytkownika to standardowy wzorzec Django, ale w klasach
    # bazowych (AbstractBaseUser, PermissionsMixin) `objects` jest ClassVar-em,
    # więc przypisanie instancji wygląda dla checkera na niezgodne nadpisanie.
    objects: CustomUserManager = CustomUserManager()  # pyrefly: ignore[bad-override]

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Użytkownik"
        verbose_name_plural = "Użytkownicy"
        constraints = [
            models.CheckConstraint(
                condition=~Q(username=""), name="accounts_user_username_not_empty"
            ),
        ]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def save(self, *args, **kwargs):
        """Zapisuje konto; bez nazwy nadaje unikalne `anon<liczba>` z ponowieniem."""
        if self.username:
            return super().save(*args, **kwargs)

        if kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = {*kwargs["update_fields"], "username"}
        for _ in range(ANON_USERNAME_MAX_ATTEMPTS):
            self.username = generate_anon_username()
            if self._anon_username_taken():
                continue
            try:
                # Savepoint: wyścig z równoległym zapisem kończy się IntegrityError,
                # po którym zewnętrzna transakcja musi dalej działać.
                with transaction.atomic(using=kwargs.get("using")):
                    return super().save(*args, **kwargs)
            except IntegrityError:
                if not self._anon_username_taken():
                    self.username = ""
                    raise
        self.username = ""
        raise IntegrityError("Nie udało się nadać unikalnej nazwy użytkownika.")

    def _anon_username_taken(self) -> bool:
        """Czy nazwa jest zajęta przez inne konto (bez względu na wielkość liter)."""
        return (
            type(self)
            .objects.filter(username__iexact=self.username)
            .exclude(pk=self.pk)
            .exists()
        )


# Podmiot zamówień, koszyka i zgód: zalogowane konto albo `None` dla gościa.
# Anonim (`AnonymousUser`) tu nie trafia — widoki zamieniają go na `None`
# w `user_of()`, więc serwisy nie muszą pytać o `is_authenticated`.
type Customer = CustomUser | None
