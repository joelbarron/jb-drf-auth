import random
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.exceptions import APIException, AuthenticationFailed, Throttled

from jb_drf_auth.conf import get_setting
from jb_drf_auth.services.client import ClientService
from jb_drf_auth.services.tokens import TokensService
from jb_drf_auth.utils import (
    get_otp_model_cls,
    get_profile_model_cls,
    get_sms_message,
    get_sms_log_model_cls,
    get_sms_provider,
    normalize_phone_number,
)


User = get_user_model()


class SmsDeliveryError(APIException):
    status_code = 503
    default_detail = _("No se pudo enviar el codigo. Intenta mas tarde.")
    default_code = "sms_delivery_error"


class OtpService:
    @staticmethod
    def _build_phone_fallback_email(phone):
        """
        Build a deterministic synthetic email for phone-only OTP sign in.
        """
        digits = "".join(ch for ch in str(phone or "") if ch.isdigit()) or "unknown"
        return f"phone_{digits}@otp.local"

    @staticmethod
    def request_otp_code(data):
        otp_length = get_setting("OTP_LENGTH")
        max_value = (10**otp_length) - 1
        code = f"{random.randint(0, max_value):0{otp_length}d}"
        channel = data["channel"]

        email = data.get("email")
        phone = data.get("phone")
        if phone:
            try:
                phone = normalize_phone_number(phone)
            except ValueError as exc:
                raise serializers.ValidationError({"phone": str(exc)}) from exc

        otp_model = get_otp_model_cls()
        cooldown_seconds = get_setting("OTP_RESEND_COOLDOWN_SECONDS")
        now = timezone.now()
        latest_qs = otp_model.objects.filter(
            is_used=False,
            channel=channel,
        )
        if email:
            latest_qs = latest_qs.filter(email=email)
        if phone:
            latest_qs = latest_qs.filter(phone=phone)

        latest = latest_qs.order_by("-id").first()
        if latest and latest.last_sent_at:
            seconds_since = (now - latest.last_sent_at).total_seconds()
            if seconds_since < cooldown_seconds:
                raise Throttled(detail=_("Debes esperar antes de solicitar otro codigo."))

        if channel == "sms":
            try:
                sms_log_model = get_sms_log_model_cls()
            except RuntimeError as exc:
                raise serializers.ValidationError(
                    {"detail": _("Configura JB_DRF_AUTH_SMS_LOG_MODEL para usar SMS.")}
                ) from exc
            sms_provider = get_sms_provider()
            ttl_minutes = max(1, int(get_setting("OTP_TTL_SECONDS") / 60))
            message = get_sms_message(code, ttl_minutes)
            try:
                sms_provider.send_sms(phone, message)
                otp = otp_model.objects.create(
                    email=email,
                    phone=phone,
                    code=code,
                    channel=channel,
                    valid_until=now + timezone.timedelta(seconds=get_setting("OTP_TTL_SECONDS")),
                    last_sent_at=now,
                )
                sms_log_model.objects.create(
                    phone=phone,
                    message=message,
                    provider=get_setting("SMS_PROVIDER"),
                    status="sent",
                )
            except Exception as exc:
                sms_log_model.objects.create(
                    phone=phone,
                    message=message,
                    provider=get_setting("SMS_PROVIDER"),
                    status="failed",
                    error_message=str(exc),
                )
                raise SmsDeliveryError() from exc
        else:
            otp = otp_model.objects.create(
                email=email,
                phone=phone,
                code=code,
                channel=channel,
                valid_until=now + timezone.timedelta(seconds=get_setting("OTP_TTL_SECONDS")),
                last_sent_at=now,
            )
            print("Sending OTP code:", code)

        return {"detail": _("Código enviado exitosamente."), "channel": otp.channel}

    @staticmethod
    def verify_otp_code(data):
        code = data.get("code")
        email = data.get("email")
        phone = data.get("phone")
        client = data.get("client")
        device_data = data.get("device", None)
        role = data.get("role")

        if phone:
            try:
                phone = normalize_phone_number(phone)
            except ValueError as exc:
                raise serializers.ValidationError({"phone": str(exc)}) from exc

        otp_model = get_otp_model_cls()
        now = timezone.now()
        otp = otp_model.objects.filter(
            is_used=False,
            valid_until__gte=now,
        )
        if email:
            otp = otp.filter(email=email)
        if phone:
            otp = otp.filter(phone=phone)

        otp = otp.order_by("-id").first()
        if not otp:
            raise AuthenticationFailed(_("Codigo invalido o expirado."))

        max_attempts = get_setting("OTP_MAX_ATTEMPTS")
        if otp.attempts >= max_attempts:
            raise Throttled(detail=_("Se excedieron los intentos permitidos."))

        if otp.code != code:
            otp.attempts += 1
            otp.save(update_fields=["attempts"])
            raise AuthenticationFailed(_("Codigo invalido o expirado."))

        otp.is_used = True
        otp.save(update_fields=["is_used"])

        email = (otp.email or "").strip() or None
        phone = (otp.phone or "").strip() or None

        user = None
        if email:
            user = User.objects.filter(email=email).first()
        elif phone:
            user = User.objects.filter(phone=phone).first()

        if not user:
            create_email = email or OtpService._build_phone_fallback_email(phone)
            user = User.objects.create_user(
                email=create_email,
                phone=phone,
                is_active=True,
            )

            profile_model = get_profile_model_cls()
            profile_model.objects.create(
                user=user,
                role=role or get_setting("DEFAULT_PROFILE_ROLE"),
                is_default=True,
            )

        if not getattr(user, "is_verified", True):
            user.is_verified = True
            user.save(update_fields=["is_verified"])

        profile = user.get_default_profile()
        tokens = TokensService.get_tokens_for_user(user, profile)
        return ClientService.response_for_client(client, user, profile, tokens, device_data)
