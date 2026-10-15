# Linki z maili allauth składane z `FRONTEND_LINK_BASE` (components/email.py,
# ADR 0038). Weryfikacja e-maila i reset hasła idą kodem, więc zostają tylko
# klucze, które allauth wciąż wstawia do maili (mail do nieznanego konta).
HEADLESS_FRONTEND_URLS = {
    "account_reset_password": f"{FRONTEND_LINK_BASE}/account/reset-password",  # noqa: F821
    "account_signup": f"{FRONTEND_LINK_BASE}/signup",  # noqa: F821
}
