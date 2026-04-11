import os

# Trwałość sesji web: domyślnie 14 dni.
# - Nie wygaszaj przy zamknięciu przeglądarki.
# - Przedłużaj TTL przy każdej aktywności (sliding session).
SESSION_COOKIE_AGE = int(
    os.environ.get("SESSION_COOKIE_AGE", str(60 * 60 * 24 * 14))
)  # 14 dni
SESSION_EXPIRE_AT_BROWSER_CLOSE = os.environ.get(
    "SESSION_EXPIRE_AT_BROWSER_CLOSE", False
)
SESSION_SAVE_EVERY_REQUEST = os.environ.get("SESSION_SAVE_EVERY_REQUEST", True)


