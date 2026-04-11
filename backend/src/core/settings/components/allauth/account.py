ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]

ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED = True
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_MAX_ATTEMPTS = 3
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_TIMEOUT = 900

ACCOUNT_LOGIN_BY_CODE_ENABLED = True
ACCOUNT_LOGIN_BY_CODE_SUPPORTS_RESEND = True
ACCOUNT_LOGIN_BY_CODE_TIMEOUT = 180

ACCOUNT_PREVENT_ENUMERATION = True
ACCOUNT_SESSION_REMEMBER = True

ACCOUNT_ADAPTER = "core.services.mail.AsyncAccountAdapter"

ACCOUNT_RATE_LIMITS = {
    "login": "10/minute",
    "signup": "10/minute",
    "password_reset": "10/minute",
    "password_set": "10/minute",
    "email_verification": "10/minute",
    "email_verification_by_code": "10/minute",
    "login_by_code": "10/minute",
    "login_by_code_resend": "10/minute",
    "webauthn_login_request": "10/minute",
    "webauthn_login_confirm": "10/minute",
    "webauthn_setup_request": "10/minute",
    "webauthn_setup_confirm": "10/minute",
}
