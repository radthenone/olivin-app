"""
Django middleware configuration.
"""
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'pack_logger.middleware.ApiLoggingMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "allauth.account.middleware.AccountMiddleware",
    'djangorestframework_camel_case.middleware.CamelCaseMiddleWare',
]
