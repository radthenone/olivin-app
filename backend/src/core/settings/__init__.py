"""
Django settings management with split-settings.
"""

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
include(*base_settings, optional('local.py'))