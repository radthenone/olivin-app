"""
Email configuration.
"""

import os

# Email configuration
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# Backend używany TYLKO w workerze (żeby nie zrobić pętli)
ACTUAL_EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"


EMAIL_HOST = str(os.environ.get("EMAIL_HOST", "localhost"))
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 1025))
EMAIL_HOST_USER = str(os.environ.get("EMAIL_HOST_USER", ""))
EMAIL_HOST_PASSWORD = str(os.environ.get("EMAIL_HOST_PASSWORD", ""))
EMAIL_USE_TLS = bool(int(os.environ.get("EMAIL_USE_TLS", 0)))
DEFAULT_FROM_EMAIL = str(os.environ.get("DEFAULT_FROM_EMAIL", "noreply@example.com"))

# Adres właściciela sklepu — trafiają tu wiadomości o zdarzeniach, które
# zmieniają katalog, jak zatwierdzenie kursu kruszcu (ADR 0022).
SHOP_OWNER_EMAIL = str(
    os.environ.get("SHOP_OWNER_EMAIL")
    or os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
)

# Jedyna baza linków w mailach (ADR 0038): domena webu (Next). Na dev
# `http://localhost:3000`, w produkcji kanoniczna domena bez przekierowań.
FRONTEND_URL = str(os.environ.get("FRONTEND_URL", "http://localhost:3000")).rstrip("/")
# Prefiks `/pl` domyślny; `common.languages.localized_link` podmienia go na
# język odbiorcy maila (`PreferredLanguage`, ADR 0035, #316).
FRONTEND_LINK_BASE = f"{FRONTEND_URL}/pl"

# Sekret endpointu rewalidacji keszu katalogu na webie (`/api/revalidate`,
# ADR 0034, #318). Pusty (dev, testy) → backend nie woła webu.
REVALIDATE_SECRET = os.environ.get("REVALIDATE_SECRET", "")

# Linki z maili newslettera (#203) prowadzą na ekrany web, które wołają API
# potwierdzenia i wypisu. `{token}` podstawia backend.
NEWSLETTER_CONFIRM_URL = f"{FRONTEND_LINK_BASE}/newsletter/confirm/{{token}}"
NEWSLETTER_UNSUBSCRIBE_URL = f"{FRONTEND_LINK_BASE}/newsletter/unsubscribe/{{token}}"

# Publiczny adres API — nagłówek `List-Unsubscribe` (RFC 8058, #314) wskazuje
# endpoint backendu, bo skrzynka wysyła tam POST bez udziału webu.
BACKEND_URL = str(os.environ.get("BACKEND_URL", "http://localhost:8020")).rstrip("/")

# Linki z przypomnienia o koszyku (#208): koszyk i zmiana zgód marketingowych.
CART_URL = f"{FRONTEND_LINK_BASE}/cart"
NOTIFICATION_PREFERENCES_URL = f"{FRONTEND_LINK_BASE}/account/notifications"
