from django.db import migrations
from django.db.models import Q

from apps.accounts.usernames import generate_anon_username


def fill_empty_usernames(apps, schema_editor):
    """Nadaje `anon<liczba>` kontom bez nazwy (#195); istniejących nazw nie rusza."""
    user_model = apps.get_model("accounts", "CustomUser")
    for user in user_model.objects.filter(Q(username__isnull=True) | Q(username="")):
        username = generate_anon_username()
        while user_model.objects.filter(username__iexact=username).exists():
            username = generate_anon_username()
        user.username = username
        user.save(update_fields=["username"])


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_profile_membership_profile_membership_granted_at"),
    ]

    # Wstecz: nadane nazwy zostają (pole po cofnięciu 0005 znów dopuszcza NULL).
    operations = [
        migrations.RunPython(fill_empty_usernames, migrations.RunPython.noop),
    ]
