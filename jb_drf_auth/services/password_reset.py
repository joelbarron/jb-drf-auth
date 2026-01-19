from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from jb_drf_auth.conf import get_setting


User = get_user_model()


class PasswordResetService:
    @staticmethod
    def send_reset_email(email: str) -> None:
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        frontend_url = get_setting("FRONTEND_URL") or ""
        reset_url = f"{frontend_url}/reset-password/?uid={uid}&token={token}"

        send_mail(
            subject="Restablece tu contraseña",
            message=f"Hola, restablece tu contraseña haciendo clic aqui:\n{reset_url}",
            from_email=get_setting("DEFAULT_FROM_EMAIL"),
            recipient_list=[user.email],
            fail_silently=False,
        )

    @staticmethod
    def reset_password(uidb64: str, token: str, new_password: str) -> bool:
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            return False

        if default_token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return True
        return False

    @staticmethod
    def change_password(user: User, old_password: str, new_password: str) -> bool:
        if not check_password(old_password, user.password):
            return False
        user.set_password(new_password)
        user.save()
        return True
