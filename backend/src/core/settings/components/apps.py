"""
Django applications configuration.
"""
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'corsheaders',
    'rest_framework',
    "django_celery_beat",
    "djangorestframework_camel_case",
    "storages",
    "rest_framework.authtoken",
    "rest_framework_simplejwt",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.mfa",
    'django_celery_results',
]

APPLICATION_APPS = [
    'apps.accounts',
    'apps.orders',
    'apps.payments',
    'apps.shipping',
    'apps.reviews',
    'apps.inventory',
    'apps.discounts',
    'apps.notifications',
    'apps.analytics',
    'apps.categories',
    'apps.products',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + APPLICATION_APPS
