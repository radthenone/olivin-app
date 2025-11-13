#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

python manage.py shell << END
import os
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f'✅ Superuser {username} created')
else:
    print(f'ℹ️  Superuser {username} already exists')

# Create token for API access
from rest_framework.authtoken.models import Token
user = User.objects.get(username=username)
token, created = Token.objects.get_or_create(user=user)
if created:
    print(f'🔑 Token created for {username}')
END