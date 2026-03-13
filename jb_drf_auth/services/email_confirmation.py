from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext as _
from rest_framework import serializers

from jb_drf_auth.conf import get_setting
from jb_drf_auth.utils import get_email_log_model_cls, get_email_provider, render_email_template


class EmailConfirmationService:
    @staticmethod
    def _is_deliverable_email(email: str | None) -> bool:
        value = (email or "").strip().lower()
        if not value:
            return False
        if value.endswith("@otp.local") or value.endswith("@phone.local"):
            return False
        return "@" in value

    @staticmethod
    def send_verification_email(user, raise_on_fail: bool = True) -> bool:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        frontend_url = get_setting("FRONTEND_URL") or ""
        verify_url = f"{frontend_url}/verify-email/?uid={uid}&token={token}"

        subject, text_body, html_body = render_email_template(
            "email_confirmation",
            {
                "user_email": user.email,
                "verify_url": verify_url,
            },
        )

        try:
            email_log_model = get_email_log_model_cls()
        except RuntimeError as exc:
            if raise_on_fail:
                raise serializers.ValidationError(
                    {"detail": _("Configura JB_DRF_AUTH_EMAIL_LOG_MODEL para usar email.")}
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
                template_name="email_confirmation",
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
                template_name="email_confirmation",
            )
            if raise_on_fail:
                raise serializers.ValidationError(
                    {"detail": _("No se pudo enviar el correo. Intenta más tarde.")}
                ) from exc
            return False

    @staticmethod
    def send_account_created_email(user, raise_on_fail: bool = False) -> bool:
        user_email = (getattr(user, "email", "") or "").strip()
        if not EmailConfirmationService._is_deliverable_email(user_email):
            return False

        subject, text_body, html_body = render_email_template(
            "account_created",
            {
                "user_email": user_email,
            },
        )

        try:
            email_log_model = get_email_log_model_cls()
        except RuntimeError as exc:
            if raise_on_fail:
                raise serializers.ValidationError(
                    {"detail": _("Configura JB_DRF_AUTH_EMAIL_LOG_MODEL para usar email.")}
                ) from exc
            return False

        provider = get_email_provider()
        try:
            provider.send_email(user_email, subject, text_body, html_body)
            email_log_model.objects.create(
                to_email=user_email,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
                provider=get_setting("EMAIL_PROVIDER"),
                status="sent",
                template_name="account_created",
            )
            return True
        except Exception as exc:
            email_log_model.objects.create(
                to_email=user_email,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
                provider=get_setting("EMAIL_PROVIDER"),
                status="failed",
                error_message=str(exc),
                template_name="account_created",
            )
            if raise_on_fail:
                raise serializers.ValidationError(
                    {"detail": _("No se pudo enviar el correo. Intenta más tarde.")}
                ) from exc
            return False
