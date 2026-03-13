from __future__ import annotations

from typing import Any, Optional

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, Throttled

from jb_drf_auth.conf import get_setting
from jb_drf_auth.utils import get_otp_model_cls, get_profile_model_cls, normalize_phone_number


User = get_user_model()


class AccountProvisioningService:
    """Provision user/profile and optionally trigger account verification."""

    @staticmethod
    def _normalize_email(value: Optional[str]) -> Optional[str]:
        normalized = (value or "").strip().lower()
        return normalized or None

    @staticmethod
    def _normalize_phone(value: Optional[str]) -> Optional[str]:
        raw = (value or "").strip()
        if not raw:
            return None
        return raw

    @staticmethod
    def _supports_field(model_cls: Any, field_name: str) -> bool:
        try:
            model_cls._meta.get_field(field_name)
            return True
        except Exception:
            return False

    @classmethod
    def _build_profile_kwargs(
        cls,
        user,
        role: Optional[str],
        profile_data: Optional[dict[str, Any]],
    ) -> dict[str, Any]:
        profile_model = get_profile_model_cls()
        kwargs: dict[str, Any] = {
            "user": user,
            "role": role or get_setting("DEFAULT_PROFILE_ROLE"),
            "is_default": True,
        }
        if not profile_data:
            return kwargs

        for key, value in profile_data.items():
            if not cls._supports_field(profile_model, key):
                continue
            kwargs[key] = value

        return kwargs

    @classmethod
    def ensure_email_available(cls, email: Optional[str], exclude_user_id: Optional[int] = None):
        normalized = cls._normalize_email(email)
        if not normalized:
            raise serializers.ValidationError({"email": _("Debes ingresar un correo válido.")})

        qs = User.objects.filter(email__iexact=normalized)
        if exclude_user_id:
            qs = qs.exclude(id=exclude_user_id)
        if qs.exists():
            raise serializers.ValidationError({"email": _("Ya existe un usuario con este correo.")})

    @classmethod
    def ensure_phone_available(cls, phone: Optional[str], exclude_user_id: Optional[int] = None):
        if not cls._supports_field(User, "phone"):
            return

        normalized = cls._normalize_phone(phone)
        if not normalized:
            return

        qs = User.objects.filter(phone=normalized)
        if exclude_user_id:
            qs = qs.exclude(id=exclude_user_id)
        if qs.exists():
            raise serializers.ValidationError({"phone": _("Ya existe un usuario con este teléfono.")})

    @classmethod
    def _resolve_channel(
        cls,
        channel: str,
        *,
        has_email: bool,
        has_phone: bool,
        allow_fallback: bool,
    ) -> tuple[str, bool]:
        requested = (channel or "auto").strip().lower()
        if requested not in {"auto", "email", "sms"}:
            raise serializers.ValidationError(
                {"verification_channel": _("Canal de verificación inválido. Usa: auto, email o sms.")}
            )

        if requested == "auto":
            if has_phone:
                return "sms", False
            if has_email:
                return "email", False
            raise serializers.ValidationError(
                {"detail": _("No hay email ni teléfono disponibles para enviar verificación.")}
            )

        if requested == "email":
            if has_email:
                return "email", False
            if allow_fallback and has_phone:
                return "sms", True
            raise serializers.ValidationError(
                {"email": _("No hay correo disponible para enviar verificación por email.")}
            )

        # requested == "sms"
        if has_phone:
            return "sms", False
        if allow_fallback and has_email:
            return "email", True
        raise serializers.ValidationError(
            {"phone": _("No hay teléfono disponible para enviar verificación por SMS.")}
        )

    @classmethod
    def send_verification(
        cls,
        *,
        user,
        email: Optional[str],
        phone: Optional[str],
        channel: str = "auto",
        allow_fallback: bool = True,
        raise_on_fail: bool = False,
    ) -> dict[str, Any]:
        # Lazy imports avoid circular imports when services package is initialized.
        from jb_drf_auth.services.email_confirmation import EmailConfirmationService
        from jb_drf_auth.services.otp import OtpService

        normalized_email = cls._normalize_email(email)
        raw_phone = cls._normalize_phone(phone)
        normalized_phone = None
        phone_normalization_error = None
        if raw_phone:
            try:
                normalized_phone = normalize_phone_number(raw_phone)
            except ValueError as exc:
                phone_normalization_error = str(exc)
        requested_channel = str(channel or "auto").strip().lower()
        has_email = bool(normalized_email)
        has_phone = bool(normalized_phone)

        if (
            requested_channel in {"sms", "auto"}
            and raw_phone
            and not has_phone
            and not (allow_fallback and has_email)
        ):
            raise serializers.ValidationError(
                {"phone": phone_normalization_error or _("El teléfono no es válido para OTP.")}
            )

        resolved_channel, fallback_used = cls._resolve_channel(
            requested_channel,
            has_email=has_email,
            has_phone=has_phone,
            allow_fallback=allow_fallback,
        )

        if resolved_channel == "email":
            sent = EmailConfirmationService.send_verification_email(user, raise_on_fail=raise_on_fail)
            return {
                "requested": True,
                "sent": bool(sent),
                "channel": "email",
                "fallback_used": fallback_used,
            }

        OtpService.request_otp_code(
            {
                "channel": "sms",
                "email": normalized_email,
                "phone": normalized_phone,
            }
        )
        return {
            "requested": True,
            "sent": True,
            "channel": "sms",
            "fallback_used": fallback_used,
        }

    @classmethod
    def verify_identity_otp(
        cls,
        *,
        code: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        channel: Optional[str] = "sms",
    ) -> dict[str, Any]:
        normalized_email = cls._normalize_email(email)
        raw_phone = cls._normalize_phone(phone)
        normalized_phone = None
        if raw_phone:
            try:
                normalized_phone = normalize_phone_number(raw_phone)
            except ValueError:
                normalized_phone = raw_phone
        otp_code = str(code or "").strip()
        channel_value = str(channel or "sms").strip().lower()

        if not otp_code:
            raise serializers.ValidationError({"code": _("Debes ingresar el código OTP.")})
        if not normalized_email and not normalized_phone:
            raise serializers.ValidationError(
                {"detail": _("Debes proporcionar un email o un teléfono para verificar.")}
            )
        if channel_value not in {"sms", "email"}:
            raise serializers.ValidationError(
                {"channel": _("Canal inválido. Usa sms o email.")}
            )

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
            raise AuthenticationFailed(_("Código inválido o expirado."))

        max_attempts = get_setting("OTP_MAX_ATTEMPTS")
        if int(getattr(otp, "attempts", 0) or 0) >= int(max_attempts):
            raise Throttled(detail=_("Se excedieron los intentos permitidos."))

        if str(getattr(otp, "code", "")).strip() != otp_code:
            otp.attempts = int(getattr(otp, "attempts", 0) or 0) + 1
            otp.save(update_fields=["attempts"])
            raise AuthenticationFailed(_("Código inválido o expirado."))

        otp.is_used = True
        otp.save(update_fields=["is_used"])

        otp_email = cls._normalize_email(getattr(otp, "email", None))
        otp_phone = (getattr(otp, "phone", None) or "").strip() or None

        user = None
        if otp_email:
            user = User.objects.filter(email__iexact=otp_email).first()
        if not user and otp_phone and cls._supports_field(User, "phone"):
            user = User.objects.filter(phone=otp_phone).first()

        if not user:
            raise serializers.ValidationError(
                {"detail": _("No se encontró un usuario asociado al código OTP.")}
            )

        if cls._supports_field(User, "is_verified") and not getattr(user, "is_verified", True):
            user.is_verified = True
            user.save(update_fields=["is_verified"])

        return {
            "detail": _("Cuenta verificada exitosamente."),
            "verified": True,
            "channel": channel_value,
            "user_id": user.id,
        }

    @classmethod
    def provision_account(
        cls,
        *,
        email: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        phone: Optional[str] = None,
        is_active: bool = True,
        is_verified: Optional[bool] = None,
        role: Optional[str] = None,
        profile_data: Optional[dict[str, Any]] = None,
        terms_and_conditions_accepted: bool = False,
        send_verification: bool = False,
        verification_channel: str = "auto",
        allow_verification_fallback: bool = True,
        verification_raise_on_fail: bool = False,
    ) -> dict[str, Any]:
        normalized_email = cls._normalize_email(email)
        normalized_phone = cls._normalize_phone(phone)

        cls.ensure_email_available(normalized_email)
        cls.ensure_phone_available(normalized_phone)

        user_kwargs: dict[str, Any] = {
            "email": normalized_email,
            "username": username,
            "password": password,
            "is_active": is_active,
        }
        if cls._supports_field(User, "phone"):
            user_kwargs["phone"] = normalized_phone
        if is_verified is not None and cls._supports_field(User, "is_verified"):
            user_kwargs["is_verified"] = is_verified

        user = User.objects.create_user(**user_kwargs)

        if terms_and_conditions_accepted and cls._supports_field(User, "terms_and_conditions"):
            user.terms_and_conditions = timezone.now()
            user.save(update_fields=["terms_and_conditions"])

        profile_model = get_profile_model_cls()
        profile = profile_model.objects.create(
            **cls._build_profile_kwargs(user=user, role=role, profile_data=profile_data)
        )

        verification_result = {
            "requested": False,
            "sent": False,
            "channel": None,
            "fallback_used": False,
        }
        if send_verification:
            verification_result = cls.send_verification(
                user=user,
                email=normalized_email,
                phone=normalized_phone,
                channel=verification_channel,
                allow_fallback=allow_verification_fallback,
                raise_on_fail=verification_raise_on_fail,
            )

        return {
            "user": user,
            "profile": profile,
            "verification": verification_result,
        }
