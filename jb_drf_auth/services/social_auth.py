import uuid
import logging
from urllib.error import URLError
from urllib.request import urlopen

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import status

from jb_drf_auth.conf import get_setting, get_social_settings
from jb_drf_auth.exceptions import SocialAuthError
from jb_drf_auth.services.client import ClientService
from jb_drf_auth.services.tokens import TokensService
from jb_drf_auth.utils import (
    get_profile_model_cls,
    get_social_account_model_cls,
    get_social_provider,
)


User = get_user_model()
logger = logging.getLogger("jb_drf_auth.services.social_auth")


class SocialAuthService:
    @staticmethod
    def _normalize_username(base: str) -> str:
        value = (base or "social").strip().lower().replace(" ", "_")
        if not value:
            value = "social"
        return value[:140]

    @staticmethod
    def _build_unique_username(provider: str, provider_user_id: str, email: str | None) -> str:
        if email and "@" in email:
            base = SocialAuthService._normalize_username(email.split("@")[0])
        else:
            base = SocialAuthService._normalize_username(f"{provider}_{provider_user_id}")

        candidate = base
        counter = 1
        while User.objects.filter(username=candidate).exists():
            counter += 1
            suffix = f"_{counter}"
            candidate = f"{base[: max(1, 150 - len(suffix))]}{suffix}"
        return candidate

    @staticmethod
    def _create_user_from_identity(identity, terms_accepted: bool, role: str | None = None):
        social_settings = get_social_settings()
        require_verified = social_settings.get("REQUIRE_VERIFIED_EMAIL", True)
        if require_verified and not identity.email_verified:
            raise SocialAuthError(
                _("Social provider did not return a verified email."),
                status_code=status.HTTP_400_BAD_REQUEST,
                code="social_email_not_verified",
            )

        if not identity.email:
            raise SocialAuthError(
                _("Social provider did not return a valid email."),
                status_code=status.HTTP_400_BAD_REQUEST,
                code="social_email_missing",
            )

        if get_setting("TERMS_AND_CONDITIONS_REQUIRED") and not terms_accepted:
            raise SocialAuthError(
                _("Terms and conditions must be accepted."),
                status_code=status.HTTP_400_BAD_REQUEST,
                code="terms_required",
            )

        username = SocialAuthService._build_unique_username(
            identity.provider, identity.provider_user_id, identity.email
        )
        user = User.objects.create_user(
            email=identity.email,
            username=username,
            password=None,
            is_active=True,
        )
        user.set_unusable_password()

        update_fields = []
        if hasattr(user, "is_verified"):
            user.is_verified = bool(identity.email_verified)
            update_fields.append("is_verified")
        if terms_accepted and hasattr(user, "terms_and_conditions"):
            user.terms_and_conditions = timezone.now()
            update_fields.append("terms_and_conditions")
        if update_fields:
            update_fields.append("password")
            user.save(update_fields=update_fields)
        else:
            user.save()

        profile_model = get_profile_model_cls()
        profile_model.objects.create(
            user=user,
            first_name=identity.first_name,
            last_name_1=identity.last_name_1,
            role=role or get_setting("DEFAULT_PROFILE_ROLE"),
            is_default=True,
        )
        logger.info(
            "social_user_created provider=%s user_id=%s has_email=%s",
            identity.provider,
            getattr(user, "id", None),
            bool(identity.email),
        )
        return user

    @staticmethod
    def _sync_profile_picture(profile, picture_url: str | None):
        social_settings = get_social_settings()
        if not social_settings.get("SYNC_PICTURE_ON_LOGIN", True):
            return
        if not picture_url or not hasattr(profile, "picture"):
            return

        timeout = social_settings.get("PICTURE_DOWNLOAD_TIMEOUT_SECONDS", 5)
        max_bytes = int(social_settings.get("PICTURE_MAX_BYTES", 5 * 1024 * 1024))
        allowed_types = social_settings.get("PICTURE_ALLOWED_CONTENT_TYPES") or ()
        allowed_types = {str(value).lower() for value in allowed_types}
        try:
            with urlopen(picture_url, timeout=timeout) as response:
                content_type = response.headers.get("Content-Type", "").lower()
                content_type = content_type.split(";")[0].strip()
                if not content_type.startswith("image/"):
                    return
                if allowed_types and content_type not in allowed_types:
                    return
                payload = response.read(max_bytes + 1)
        except (URLError, TimeoutError, ValueError, OSError):
            logger.warning(
                "social_picture_download_failed profile_id=%s picture_url_present=%s",
                getattr(profile, "pk", None),
                bool(picture_url),
            )
            return

        if not payload:
            return
        if len(payload) > max_bytes:
            return

        extension = "jpg"
        if "png" in content_type:
            extension = "png"
        elif "webp" in content_type:
            extension = "webp"

        filename = f"social-{profile.pk}-{uuid.uuid4().hex[:10]}.{extension}"
        profile.picture.save(filename, ContentFile(payload), save=True)
        logger.info(
            "social_picture_synced profile_id=%s bytes=%s content_type=%s",
            getattr(profile, "pk", None),
            len(payload),
            content_type,
        )

    @staticmethod
    def login_or_register(
        provider_name: str,
        payload: dict,
        client: str,
        device_data: dict | None,
        role: str | None = None,
        terms_and_conditions_accepted: bool = False,
    ):
        logger.info(
            "social_login_or_register_started provider=%s client=%s",
            provider_name,
            client,
        )
        social_provider = get_social_provider(provider_name)
        identity = social_provider.authenticate(payload)

        social_account_model = get_social_account_model_cls()
        social_settings = get_social_settings()
        user = None
        user_created = False
        linked_existing = False

        social_account = social_account_model.objects.filter(
            provider=identity.provider,
            provider_user_id=identity.provider_user_id,
        ).select_related("user").first()

        if social_account:
            user = social_account.user
            logger.info(
                "social_account_found provider=%s user_id=%s",
                identity.provider,
                getattr(user, "id", None),
            )
        else:
            if social_settings.get("LINK_BY_EMAIL", True) and identity.email:
                user = User.objects.filter(email__iexact=identity.email).first()
                linked_existing = user is not None
                if linked_existing:
                    logger.info(
                        "social_linked_existing_by_email provider=%s user_id=%s",
                        identity.provider,
                        getattr(user, "id", None),
                    )

            if user is None:
                if not social_settings.get("AUTO_CREATE_USER", True):
                    raise SocialAuthError(
                        _("No account is linked for this social provider."),
                        status_code=status.HTTP_400_BAD_REQUEST,
                        code="social_account_not_linked",
                    )
                user = SocialAuthService._create_user_from_identity(
                    identity=identity,
                    terms_accepted=terms_and_conditions_accepted,
                    role=role,
                )
                user_created = True

        social_account, created_or_updated = social_account_model.objects.update_or_create(
            provider=identity.provider,
            provider_user_id=identity.provider_user_id,
            defaults={
                "user": user,
                "email": identity.email,
                "email_verified": bool(identity.email_verified),
                "picture_url": identity.picture_url,
                "raw_response": identity.raw_response or {},
                "last_login_at": timezone.now(),
            },
        )

        profile = user.get_default_profile()
        if profile is None:
            profile_model = get_profile_model_cls()
            profile = profile_model.objects.create(
                user=user,
                first_name=identity.first_name,
                last_name_1=identity.last_name_1,
                role=role or get_setting("DEFAULT_PROFILE_ROLE"),
                is_default=True,
            )

        SocialAuthService._sync_profile_picture(profile, identity.picture_url)

        tokens = TokensService.get_tokens_for_user(
            user=user,
            profile=profile,
        )
        response = ClientService.response_for_client(client, user, profile, tokens, device_data)
        response["social_provider"] = identity.provider
        response["user_created"] = user_created
        response["linked_existing_user"] = linked_existing
        response["social_account_id"] = social_account.pk
        logger.info(
            "social_login_or_register_success provider=%s user_id=%s user_created=%s linked_existing_user=%s",
            identity.provider,
            getattr(user, "id", None),
            user_created,
            linked_existing,
        )
        return response

    @staticmethod
    def precheck(provider_name: str, payload: dict):
        social_provider = get_social_provider(provider_name)
        identity = social_provider.authenticate(payload)

        social_account_model = get_social_account_model_cls()
        social_settings = get_social_settings()
        link_by_email = bool(social_settings.get("LINK_BY_EMAIL", True))
        auto_create_user = bool(social_settings.get("AUTO_CREATE_USER", True))

        social_account = social_account_model.objects.filter(
            provider=identity.provider,
            provider_user_id=identity.provider_user_id,
        ).select_related("user").first()

        user_by_email = None
        if not social_account and link_by_email and identity.email:
            user_by_email = User.objects.filter(email__iexact=identity.email).first()

        social_account_exists = social_account is not None
        linked_existing_user = user_by_email is not None
        user_exists = social_account_exists or linked_existing_user
        would_create_user = (not user_exists) and auto_create_user

        return {
            "provider": identity.provider,
            "email": identity.email,
            "email_verified": bool(identity.email_verified),
            "social_account_exists": social_account_exists,
            "linked_existing_user": linked_existing_user,
            "user_exists": user_exists,
            "would_create_user": would_create_user,
            "can_login": social_account_exists or linked_existing_user or auto_create_user,
        }

    @staticmethod
    def link_account(user, provider_name: str, payload: dict):
        logger.info(
            "social_link_started provider=%s user_id=%s",
            provider_name,
            getattr(user, "id", None),
        )
        social_provider = get_social_provider(provider_name)
        identity = social_provider.authenticate(payload)

        social_account_model = get_social_account_model_cls()

        existing = social_account_model.objects.filter(
            provider=identity.provider,
            provider_user_id=identity.provider_user_id,
        ).select_related("user").first()
        if existing and existing.user_id != user.id:
            logger.warning(
                "social_link_rejected provider=%s target_user_id=%s existing_user_id=%s",
                identity.provider,
                getattr(user, "id", None),
                existing.user_id,
            )
            raise SocialAuthError(
                _("This social account is already linked to another user."),
                status_code=status.HTTP_400_BAD_REQUEST,
                code="social_already_linked",
            )

        social_account, created = social_account_model.objects.update_or_create(
            provider=identity.provider,
            provider_user_id=identity.provider_user_id,
            defaults={
                "user": user,
                "email": identity.email,
                "email_verified": bool(identity.email_verified),
                "picture_url": identity.picture_url,
                "raw_response": identity.raw_response or {},
                "last_login_at": timezone.now(),
            },
        )

        profile = user.get_default_profile()
        if profile is not None:
            SocialAuthService._sync_profile_picture(profile, identity.picture_url)

        logger.info(
            "social_link_success provider=%s user_id=%s created=%s",
            identity.provider,
            getattr(user, "id", None),
            created,
        )
        return {
            "detail": _("Social account linked successfully."),
            "provider": identity.provider,
            "social_account_id": social_account.pk,
            "created": created,
        }

    @staticmethod
    def unlink_account(user, provider_name: str):
        logger.info(
            "social_unlink_started provider=%s user_id=%s",
            provider_name,
            getattr(user, "id", None),
        )
        social_account_model = get_social_account_model_cls()
        social_account = social_account_model.objects.filter(
            user=user,
            provider=provider_name,
        ).first()
        if not social_account:
            logger.warning(
                "social_unlink_not_found provider=%s user_id=%s",
                provider_name,
                getattr(user, "id", None),
            )
            raise SocialAuthError(
                _("No linked social account found for this provider."),
                status_code=status.HTTP_404_NOT_FOUND,
                code="social_not_found",
            )

        social_account.delete()
        logger.info(
            "social_unlink_success provider=%s user_id=%s",
            provider_name,
            getattr(user, "id", None),
        )
        return {
            "detail": _("Social account unlinked successfully."),
            "provider": provider_name,
        }
