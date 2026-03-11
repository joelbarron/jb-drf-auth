from __future__ import annotations

from django.core import signing
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, Throttled

from jb_drf_auth.conf import get_setting
from jb_drf_auth.services.otp import OtpService
from jb_drf_auth.utils import get_otp_model_cls, normalize_phone_number


class ContactVerificationService:
    PROOF_SALT = "jb_drf_auth.contact_verification_proof"

    @staticmethod
    def _normalize_email(value):
        normalized = (value or "").strip().lower()
        return normalized or None

    @staticmethod
    def _normalize_phone(value):
        raw = (value or "").strip()
        if not raw:
            return None
        try:
            return normalize_phone_number(raw)
        except ValueError as exc:
            raise serializers.ValidationError({"phone": str(exc)}) from exc

    @classmethod
    def request_verification(cls, *, email=None, phone=None, channel="sms"):
        normalized_email = cls._normalize_email(email)
        normalized_phone = cls._normalize_phone(phone)
        channel_value = str(channel or "").strip().lower()

        OtpService.request_otp_code(
            {
                "email": normalized_email,
                "phone": normalized_phone,
                "channel": channel_value,
            }
        )
        return {
            "detail": _("Código enviado exitosamente."),
            "channel": channel_value,
            "sent": True,
        }

    @classmethod
    def _build_proof_payload(cls, *, user_id, channel, email, phone):
        now = timezone.now()
        normalized_user_id = int(user_id) if user_id else None
        return {
            "sub": normalized_user_id,
            "channel": str(channel or "").strip().lower(),
            "email": cls._normalize_email(email),
            "phone": cls._normalize_phone(phone),
            "iat": int(now.timestamp()),
        }

    @classmethod
    def _issue_proof_token(cls, payload):
        return signing.dumps(payload, salt=cls.PROOF_SALT)

    @classmethod
    def verify_proof_token(
        cls,
        token,
        *,
        user_id=None,
        channel=None,
        email=None,
        phone=None,
    ):
        ttl = int(get_setting("CONTACT_VERIFICATION_PROOF_TTL_SECONDS") or 1800)
        try:
            payload = signing.loads(token, salt=cls.PROOF_SALT, max_age=ttl)
        except signing.SignatureExpired as exc:
            raise serializers.ValidationError({"verificationProofToken": _("Token expirado.")}) from exc
        except signing.BadSignature as exc:
            raise serializers.ValidationError({"verificationProofToken": _("Token inválido.")}) from exc

        if user_id is not None:
            expected_user_id = int(user_id)
            token_user_id = payload.get("sub")
            if int(token_user_id or 0) != expected_user_id:
                raise serializers.ValidationError({"verificationProofToken": _("Token inválido para este usuario.")})

        if channel:
            expected_channel = str(channel or "").strip().lower()
            if str(payload.get("channel") or "").strip().lower() != expected_channel:
                raise serializers.ValidationError({"verificationProofToken": _("Canal de verificación inválido.")})

        if email is not None:
            expected_email = cls._normalize_email(email)
            if (payload.get("email") or None) != expected_email:
                raise serializers.ValidationError({"verificationProofToken": _("Correo no coincide con el token.")})

        if phone is not None:
            expected_phone = cls._normalize_phone(phone)
            if (payload.get("phone") or None) != expected_phone:
                raise serializers.ValidationError({"verificationProofToken": _("Teléfono no coincide con el token.")})

        return payload

    @classmethod
    def verify_code_and_issue_proof(
        cls,
        *,
        user_id=None,
        code,
        channel="sms",
        email=None,
        phone=None,
    ):
        normalized_email = cls._normalize_email(email)
        normalized_phone = cls._normalize_phone(phone)
        channel_value = str(channel or "").strip().lower()
        otp_code = str(code or "").strip()

        if not otp_code:
            raise serializers.ValidationError({"code": _("Debes ingresar el código OTP.")})

        otp_model = get_otp_model_cls()
        now = timezone.now()
        otp_qs = otp_model.objects.filter(
            is_used=False,
            valid_until__gte=now,
            channel=channel_value,
        )
        if normalized_email:
            otp_qs = otp_qs.filter(email=normalized_email)
        if normalized_phone:
            otp_qs = otp_qs.filter(phone=normalized_phone)

        otp = otp_qs.order_by("-id").first()
        if not otp:
            raise AuthenticationFailed(_("Codigo invalido o expirado."))

        max_attempts = int(get_setting("OTP_MAX_ATTEMPTS") or 5)
        if int(getattr(otp, "attempts", 0) or 0) >= max_attempts:
            raise Throttled(detail=_("Se excedieron los intentos permitidos."))

        if str(getattr(otp, "code", "")).strip() != otp_code:
            otp.attempts = int(getattr(otp, "attempts", 0) or 0) + 1
            otp.save(update_fields=["attempts"])
            raise AuthenticationFailed(_("Codigo invalido o expirado."))

        otp.is_used = True
        otp.save(update_fields=["is_used"])

        payload = cls._build_proof_payload(
            user_id=user_id,
            channel=channel_value,
            email=normalized_email,
            phone=normalized_phone,
        )
        token = cls._issue_proof_token(payload)
        ttl = int(get_setting("CONTACT_VERIFICATION_PROOF_TTL_SECONDS") or 1800)

        return {
            "detail": _("Contacto verificado correctamente."),
            "verified": True,
            "channel": channel_value,
            "verificationProofToken": token,
            "verification_proof_token": token,
            "expiresInSeconds": ttl,
            "expires_in_seconds": ttl,
        }
