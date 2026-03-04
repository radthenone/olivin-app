from django.db import models


# Create your models here.
class RoleChoices(models.TextChoices):
    CUSTOMER = "customer", "Customer"
    ADMIN = "admin", "Admin"