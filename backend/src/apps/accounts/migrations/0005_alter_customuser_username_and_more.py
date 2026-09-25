from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_fill_empty_usernames"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customuser",
            name="username",
            field=models.CharField(
                blank=True,
                max_length=150,
                unique=True,
                verbose_name="nazwa użytkownika",
            ),
        ),
        migrations.AddConstraint(
            model_name="customuser",
            constraint=models.CheckConstraint(
                condition=models.Q(("username", ""), _negated=True),
                name="accounts_user_username_not_empty",
            ),
        ),
    ]
