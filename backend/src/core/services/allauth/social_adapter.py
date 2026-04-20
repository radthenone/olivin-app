from allauth.account.internal.emailkit import valid_email_or_none
from allauth.account.utils import user_email, user_field
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email")
        name = data.get("name", "")
        user = sociallogin.user

        user.username = None
        user_email(user, valid_email_or_none(email) or "")
        name_parts = (name or "").partition(" ")
        user_field(user, "first_name", first_name or name_parts[0])
        user_field(user, "last_name", last_name or name_parts[2])

        return user

    def is_open_for_signup(self, request, sociallogin: SocialLogin) -> bool:
        email = sociallogin.account.extra_data.get("email")
        if not email:
            return False
        return super().is_open_for_signup(request, sociallogin)
