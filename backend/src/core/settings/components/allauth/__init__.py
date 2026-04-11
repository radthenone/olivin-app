from split_settings.tools import include

include("account.py", "headless.py", "mfa.py", "socialaccount.py")

ALLAUTH_HEADLESS_BACKEND = "session"
