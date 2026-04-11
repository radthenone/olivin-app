#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

python manage.py shell << END
import os
from django.contrib.auth import get_user_model

User = get_user_model()
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(email=email, password=password)
    print(f'✅ Superuser {email} created')
else:
    print(f'ℹ️  Superuser {email} already exists')

# Create token for API access
from rest_framework.authtoken.models import Token
user = User.objects.get(email=email)
token, created = Token.objects.get_or_create(user=user)
if created:
    print(f'🔑 Token created for {email}')
END