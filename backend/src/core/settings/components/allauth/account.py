ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]

ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED = True
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_MAX_ATTEMPTS = 3
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_TIMEOUT = 900
ACCOUNT_EMAIL_VERIFICATION_SUPPORTS_RESEND = True

ACCOUNT_LOGIN_BY_CODE_ENABLED = True
ACCOUNT_LOGIN_BY_CODE_SUPPORTS_RESEND = True
ACCOUNT_LOGIN_BY_CODE_TIMEOUT = 180

ACCOUNT_PREVENT_ENUMERATION = True
ACCOUNT_SESSION_REMEMBER = True

ACCOUNT_ADAPTER = "core.services.mail.AsyncAccountAdapter"

ACCOUNT_RATE_LIMITS = {
    "login": "10/m/ip",
    "login_failed": "10/m/ip,5/5m/key",
    "signup": "10/m/ip",
    "reset_password": "10/m/ip,5/m/key",
    "confirm_email": "5/m/key",
    "login_by_code": "10/m/ip,5/m/key",
    "login_by_code_resend": "3/m/key",
    "webauthn_login_request": "10/m/ip",
    "webauthn_login_confirm": "10/m/ip",
    "webauthn_setup_request": "10/m/user",
    "webauthn_setup_confirm": "10/m/user",
}
