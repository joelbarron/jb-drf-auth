from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers

from jb_drf_auth.conf import get_setting
from jb_drf_auth.utils import get_email_log_model_cls, get_email_provider, render_email_template


User = get_user_model()


class PasswordResetService:
    @staticmethod
    def send_reset_email(email: str, raise_on_fail: bool = True) -> bool:
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        frontend_url = get_setting("FRONTEND_URL") or ""
        reset_url = f"{frontend_url}/reset-password/?uid={uid}&token={token}"

        subject, text_body, html_body = render_email_template(
            "password_reset",
            {
                "user_email": user.email,
                "reset_url": reset_url,
            },
        )

        try:
            email_log_model = get_email_log_model_cls()
        except RuntimeError as exc:
            if raise_on_fail:
                raise serializers.ValidationError(
                    {"detail": "Configura JB_DRF_AUTH_EMAIL_LOG_MODEL para usar email."}
                ) from exc
            return False

        provider = get_email_provider()
        try:
            provider.send_email(user.email, subject, text_body, html_body)
            email_log_model.objects.create(
                to_email=user.email,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
                provider=get_setting("EMAIL_PROVIDER"),
                status="sent",
                template_name="password_reset",
            )
            return True
        except Exception as exc:
            email_log_model.objects.create(
                to_email=user.email,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
                provider=get_setting("EMAIL_PROVIDER"),
                status="failed",
                error_message=str(exc),
                template_name="password_reset",
            )
            if raise_on_fail:
                raise serializers.ValidationError(
                    {"detail": "No se pudo enviar el correo. Intenta mas tarde."}
                ) from exc
            return False

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
