"""
Django settings management with split-settings.
"""

import os
from split_settings.tools import include, optional

# Base settings that are always loaded
base_settings = [
    'components/apps.py',
    'components/middleware.py',
    'components/database.py',
    'components/auth.py',
    'components/storage.py',
    'components/celery.py',
    'components/email.py',
    'base.py',
]

# Environment-specific settings
# W development mode ładuj development.py, w przeciwnym razie production.py
if os.environ.get('DJANGO_DEBUG', '1') == '1' or os.environ.get('DJANGO_ENV', '').lower() == 'development':
    include(*base_settings, 'development.py', optional('local.py'))
else:
    include(*base_settings, 'production.py', optional('local.py'))