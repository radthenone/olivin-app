"""
Email configuration.
"""
import os

# Email configuration
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = str(os.environ.get("EMAIL_HOST", "localhost"))
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 1025))
EMAIL_HOST_USER = str(os.environ.get("EMAIL_HOST_USER", ""))
EMAIL_HOST_PASSWORD = str(os.environ.get("EMAIL_HOST_PASSWORD", ""))
EMAIL_USE_TLS = bool(int(os.environ.get("EMAIL_USE_TLS", 0)))
DEFAULT_FROM_EMAIL = str(os.environ.get("DEFAULT_FROM_EMAIL", "noreply@example.com"))
