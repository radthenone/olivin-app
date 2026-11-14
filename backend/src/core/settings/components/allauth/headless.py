# Linki frontendu allauth składane z `FRONTEND_LINK_BASE` (components/email.py,
# ADR 0038). Weryfikacja e-maila i reset hasła idą kodem, więc z maili zostają
# tylko klucze, które allauth wciąż wstawia do maili (mail do nieznanego konta).
# `socialaccount_login_error` obsługuje powrót po błędzie providera.
# `FRONTEND_LINK_BASE` pochodzi z wcześniej dołączonego `email.py` (split-settings).
_BASE = FRONTEND_LINK_BASE  # noqa: F821  # type: ignore[unknown-name]

HEADLESS_FRONTEND_URLS = {
    "account_reset_password": f"{_BASE}/reset-password",
    "account_signup": f"{_BASE}/signup",
    # allauth dokłada `?error=...&error_process=...`.
    "socialaccount_login_error": f"{_BASE}/auth/provider/callback",
}
