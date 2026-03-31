from __future__ import annotations

from typing import Any, Optional
from uuid import uuid4
from urllib.parse import urlencode
import logging

from django.contrib.auth import get_user_model
from django.conf import settings
from django.apps import apps
from django.core import signing
from django.core.cache import cache
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.exceptions import APIException, AuthenticationFailed

from jb_drf_auth.conf import get_setting
from jb_drf_auth.services.client import ClientService
from jb_drf_auth.services.profile_mirror import ProfileRoleMirrorService
from jb_drf_auth.services.tokens import TokensService
from jb_drf_auth.utils import (
    get_profile_model_cls,
    get_sms_log_model_cls,
    get_sms_provider,
    normalize_phone_number,
)


User = get_user_model()
logger = logging.getLogger(__name__)


class MagicLinkDeliveryError(APIException):
    status_code = 503
    default_detail = _("No se pudo enviar el enlace de acceso. Intenta más tarde.")
    default_code = "magic_link_delivery_error"


class MagicLinkService:
    TOKEN_SALT = "jb_drf_auth.magic_link"
    USED_TOKEN_CACHE_PREFIX = "jb_drf_auth.magic_link.used"

    @staticmethod
    def _ttl_seconds() -> int:
        top_level_minutes = getattr(settings, "PATIENT_MAGIC_LINK_TTL_MINUTES", None)
        if top_level_minutes is not None:
            try:
                return max(60, int(top_level_minutes) * 60)
            except (TypeError, ValueError):
                pass
        raw_value = int(get_setting("MAGIC_LINK_TTL_SECONDS") or 900)
        return max(60, raw_value)

    @staticmethod
    def _normalize_phone(value: Optional[str]) -> str:
        raw_phone = (value or "").strip()
        if not raw_phone:
            raise serializers.ValidationError({"phone": _("Debes proporcionar un teléfono válido.")})
        try:
            return normalize_phone_number(raw_phone)
        except ValueError as exc:
            raise serializers.ValidationError({"phone": str(exc)}) from exc

    @staticmethod
    def _resolve_profile(user, *, role: Optional[str], profile_id: Optional[int]):
        profile_model = get_profile_model_cls()
        profiles_qs = profile_model.objects.filter(user=user, is_active=True)

        profile_field_names = {field.name for field in profile_model._meta.get_fields()}
        if "deleted" in profile_field_names:
            profiles_qs = profiles_qs.filter(deleted=None)

        if profile_id:
            profile = profiles_qs.filter(id=profile_id).first()
            if profile:
                return profile

        normalized_role = str(role or "").strip().upper()
        if normalized_role:
            profile = profiles_qs.filter(role=normalized_role).order_by("id").first()
            if profile:
                return profile

        profile = profiles_qs.filter(is_default=True).order_by("id").first()
        if profile:
            return profile

        return profiles_qs.order_by("id").first()

    @classmethod
    def issue_token(
        cls,
        *,
        user,
        role: Optional[str] = None,
        profile_id: Optional[int] = None,
        extra_payload: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        ttl_seconds = cls._ttl_seconds()
        now = timezone.now()

        payload: dict[str, Any] = {
            "sub": int(user.id),
            "jti": uuid4().hex,
            "iat": int(now.timestamp()),
        }

        normalized_role = str(role or "").strip().upper()
        if normalized_role:
            payload["role"] = normalized_role

        if profile_id:
            payload["profile_id"] = int(profile_id)

        if isinstance(extra_payload, dict):
            payload.update(extra_payload)

        token = signing.dumps(payload, salt=cls.TOKEN_SALT)
        return {
            "token": token,
            "ttl_seconds": ttl_seconds,
            "expires_in_seconds": ttl_seconds,
            "expiresInSeconds": ttl_seconds,
        }

    @classmethod
    def build_frontend_url(cls, token: str) -> str:
        frontend_url = str(get_setting("FRONTEND_URL") or "").strip()
        if not frontend_url:
            raise serializers.ValidationError(
                {"detail": _("Configura FRONTEND_URL para enviar enlaces de acceso por SMS.")}
            )

        frontend_path = str(get_setting("MAGIC_LINK_FRONTEND_PATH") or "/sign-in").strip() or "/sign-in"
        if not frontend_path.startswith("/"):
            frontend_path = f"/{frontend_path}"

        query_param = str(get_setting("MAGIC_LINK_QUERY_PARAM") or "mlt").strip() or "mlt"
        encoded_query = urlencode({query_param: token})
        return f"{frontend_url.rstrip('/')}{frontend_path}?{encoded_query}"

    @classmethod
    def issue_sms_login_link(
        cls,
        *,
        user,
        phone: Optional[str],
        role: Optional[str] = None,
        profile_id: Optional[int] = None,
        extra_payload: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        normalized_phone = cls._normalize_phone(phone)
        token_payload = cls.issue_token(
            user=user,
            role=role,
            profile_id=profile_id,
            extra_payload=extra_payload,
        )

        token = token_payload["token"]
        ttl_seconds = int(token_payload["ttl_seconds"])
        ttl_minutes = max(1, int(ttl_seconds / 60))
        url = cls.build_frontend_url(token)
        template = get_setting("SMS_MAGIC_LINK_MESSAGE") or "Tu acceso a Mentalysis es {url}. Expira en {minutes} minutos."
        message = str(template).format(url=url, minutes=ttl_minutes)

        sms_log_model = None
        try:
            sms_log_model = get_sms_log_model_cls()
        except RuntimeError:
            sms_log_model = None

        sms_provider = get_sms_provider()
        try:
            sms_provider.send_sms(normalized_phone, message)
            if sms_log_model:
                sms_log_model.objects.create(
                    phone=normalized_phone,
                    message=message,
                    provider=get_setting("SMS_PROVIDER"),
                    status="sent",
                )
        except Exception as exc:
            if sms_log_model:
                sms_log_model.objects.create(
                    phone=normalized_phone,
                    message=message,
                    provider=get_setting("SMS_PROVIDER"),
                    status="failed",
                    error_message=str(exc),
                )
            raise MagicLinkDeliveryError() from exc

        return {
            "detail": _("Enlace de acceso enviado correctamente."),
            "sent": True,
            "channel": "sms",
            "phone": normalized_phone,
            "url": url,
            "token": token,
            "expires_in_seconds": ttl_seconds,
            "expiresInSeconds": ttl_seconds,
        }

    @classmethod
    def _mark_patient_invite_consumed(cls, *, payload: dict[str, Any], user) -> None:
        patient_id = payload.get("patient_id")
        if not patient_id:
            return

        try:
            patient_model = apps.get_model("medical", "Patient")
        except Exception:
            return

        if not patient_model:
            return

        try:
            qs = patient_model.objects.filter(id=patient_id)
            if hasattr(patient_model, "user"):
                qs = qs.filter(user=user)
            patient = qs.first()
            if not patient:
                return

            update_fields = []
            if hasattr(patient, "account_invite_status") and patient.account_invite_status != "consumed":
                patient.account_invite_status = "consumed"
                update_fields.append("account_invite_status")
            if hasattr(patient, "account_invite_last_error") and patient.account_invite_last_error is not None:
                patient.account_invite_last_error = None
                update_fields.append("account_invite_last_error")
            if update_fields:
                patient.save(update_fields=update_fields)
        except Exception:
            logger.warning(
                "patient_magic_link_consumed_status_update_failed",
                extra={"patient_id": patient_id, "user_id": getattr(user, "id", None)},
            )

    @classmethod
    def consume_token(
        cls,
        *,
        token: str,
        client: str = "web",
        role: Optional[str] = None,
        device_data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        ttl_seconds = cls._ttl_seconds()

        try:
            payload = signing.loads(token, salt=cls.TOKEN_SALT, max_age=ttl_seconds)
        except signing.SignatureExpired as exc:
            logger.info("patient_magic_link_expired")
            raise AuthenticationFailed(_("El enlace de acceso expiró.")) from exc
        except signing.BadSignature as exc:
            logger.info("patient_magic_link_invalid")
            raise AuthenticationFailed(_("El enlace de acceso no es válido.")) from exc

        jti = str(payload.get("jti") or "").strip()
        if not jti:
            raise AuthenticationFailed(_("El enlace de acceso no es válido."))

        used_cache_key = f"{cls.USED_TOKEN_CACHE_PREFIX}:{jti}"
        if not cache.add(used_cache_key, "1", timeout=ttl_seconds):
            logger.info("patient_magic_link_already_used")
            raise AuthenticationFailed(_("El enlace de acceso ya fue utilizado."))

        user_id = int(payload.get("sub") or 0)
        if not user_id:
            raise AuthenticationFailed(_("El enlace de acceso no es válido."))

        user = User.objects.filter(id=user_id).first()
        if not user:
            raise AuthenticationFailed(_("No se encontró una cuenta para este enlace de acceso."))
        if not getattr(user, "is_active", True):
            raise AuthenticationFailed(_("Esta cuenta está inactiva."))
        if getattr(user, "deleted", None):
            raise AuthenticationFailed(_("Esta cuenta está eliminada."))

        token_role = str(payload.get("role") or "").strip().upper() or None
        expected_role = str(role or "").strip().upper() or token_role
        profile = cls._resolve_profile(
            user,
            role=expected_role,
            profile_id=payload.get("profile_id"),
        )
        if not profile:
            raise AuthenticationFailed(_("No se encontró un perfil válido para iniciar sesión."))

        if expected_role and str(getattr(profile, "role", "") or "").strip().upper() != expected_role:
            raise AuthenticationFailed(_("El perfil de este enlace no coincide con el rol esperado."))

        ProfileRoleMirrorService.autocure_for_profile(profile)

        if hasattr(user, "last_login"):
            user.last_login = timezone.now()
            user.save(update_fields=["last_login"])

        tokens = TokensService.get_tokens_for_user(user=user, profile=profile)
        response = ClientService.response_for_client(client, user, profile, tokens, device_data)
        cls._mark_patient_invite_consumed(payload=payload, user=user)
        logger.info("patient_magic_link_consumed", extra={"user_id": user.id, "profile_id": profile.id})
        response["magic_link"] = {
            "consumed": True,
            "channel": "sms",
            "role": expected_role or str(getattr(profile, "role", "") or "").strip().upper(),
        }
        return response
