from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from jb_drf_auth.conf import get_setting


class EmailConfirmationService:
    @staticmethod
    def send_verification_email(user):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        frontend_url = get_setting("FRONTEND_URL") or ""
        verify_url = f"{frontend_url}/verify-email/?uid={uid}&token={token}"

        from_email = get_setting("DEFAULT_FROM_EMAIL")
        try:
            send_mail(
                subject="Verifica tu correo",
                message=f"Hola {getattr(user, 'email', '')}, verifica tu correo aqui:\n{verify_url}",
                from_email=from_email,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception:
            print(f"Email verification send failed for: {user.email}")
