import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jb_drf_auth.tests.settings")
django.setup()

from rest_framework import serializers as drf_serializers

from jb_drf_auth.providers.base import SocialIdentity
from jb_drf_auth.serializers.profile import ProfilePictureUpdateSerializer, ProfileSerializer
from jb_drf_auth.services.account_provisioning import AccountProvisioningService
from jb_drf_auth.services.login import LoginService
from jb_drf_auth.services.magic_link import MagicLinkService
from jb_drf_auth.services.me import MeService
from jb_drf_auth.services.otp import OtpService
from jb_drf_auth.services.social_auth import SocialAuthService


class ProfileMirrorIntegrationTests(unittest.TestCase):
    @patch("jb_drf_auth.serializers.profile.ProfileRoleMirrorService.is_enabled", return_value=True)
    def test_profile_serializer_blocks_manual_create_when_mirror_enabled(self, _is_enabled):
        user = SimpleNamespace(is_authenticated=True)
        request = SimpleNamespace(user=user)
        serializer = ProfileSerializer(context={"request": request})

        with self.assertRaises(drf_serializers.ValidationError) as context:
            serializer.create({})

        self.assertIn("detail", context.exception.detail)

    @patch("jb_drf_auth.services.account_provisioning.ProfileRoleMirrorService.ensure_counterpart")
    @patch("jb_drf_auth.services.account_provisioning.get_profile_model_cls")
    @patch("jb_drf_auth.services.account_provisioning.User")
    def test_account_provisioning_creates_counterpart(
        self,
        user_cls,
        get_profile_model_cls,
        ensure_counterpart,
    ):
        user = MagicMock()
        user_cls.objects.create_user.return_value = user
        profile = MagicMock()
        profile_model = MagicMock()
        profile_model.objects.create.return_value = profile
        get_profile_model_cls.return_value = profile_model

        with (
            patch.object(AccountProvisioningService, "ensure_email_available"),
            patch.object(AccountProvisioningService, "ensure_phone_available"),
            patch.object(AccountProvisioningService, "_supports_field", return_value=False),
        ):
            AccountProvisioningService.provision_account(
                email="host@example.com",
                role="HOST",
            )

        ensure_counterpart.assert_called_once_with(profile, create_missing=True)

    @patch("jb_drf_auth.services.otp.ProfileRoleMirrorService.ensure_counterpart")
    @patch("jb_drf_auth.services.otp.get_setting")
    @patch("jb_drf_auth.services.otp.EmailConfirmationService.send_account_created_email")
    @patch("jb_drf_auth.services.otp.ClientService.response_for_client")
    @patch("jb_drf_auth.services.otp.TokensService.get_tokens_for_user")
    @patch("jb_drf_auth.services.otp.get_profile_model_cls")
    @patch("jb_drf_auth.services.otp.get_otp_model_cls")
    @patch("jb_drf_auth.services.otp.User")
    def test_otp_new_user_creation_creates_counterpart(
        self,
        user_cls,
        get_otp_model_cls,
        get_profile_model_cls,
        get_tokens_for_user,
        response_for_client,
        send_account_created_email,
        get_setting,
        ensure_counterpart,
    ):
        get_setting.side_effect = lambda key: {
            "OTP_MAX_ATTEMPTS": 5,
            "DEFAULT_PROFILE_ROLE": "GUEST",
        }[key]

        otp = SimpleNamespace(
            email="",
            phone="+525512345674",
            code="123456",
            attempts=0,
            is_used=False,
            save=MagicMock(),
        )
        otp_qs = MagicMock()
        otp_qs.filter.return_value = otp_qs
        otp_qs.order_by.return_value.first.return_value = otp
        otp_model = MagicMock()
        otp_model.objects.filter.return_value = otp_qs
        get_otp_model_cls.return_value = otp_model

        user_qs = MagicMock()
        user_qs.first.return_value = None
        user_cls.objects.filter.return_value = user_qs

        created_user = MagicMock()
        created_user.is_verified = False
        created_user.get_default_profile.return_value = MagicMock()
        user_cls.objects.create_user.return_value = created_user

        created_profile = MagicMock()
        profile_model = MagicMock()
        profile_model.objects.create.return_value = created_profile
        get_profile_model_cls.return_value = profile_model

        get_tokens_for_user.return_value = {"access": "a", "refresh": "b"}
        response_for_client.return_value = {"ok": True}
        send_account_created_email.return_value = False

        OtpService.verify_otp_code(
            {
                "phone": "+525512345674",
                "code": "123456",
                "client": "web",
                "role": "HOST",
            }
        )

        ensure_counterpart.assert_called_once_with(created_profile, create_missing=True)

    @patch("jb_drf_auth.services.social_auth.ProfileRoleMirrorService.ensure_counterpart")
    @patch("jb_drf_auth.services.social_auth.get_profile_model_cls")
    @patch("jb_drf_auth.services.social_auth.get_setting")
    @patch("jb_drf_auth.services.social_auth.get_social_settings")
    @patch("jb_drf_auth.services.social_auth.User")
    def test_social_user_creation_creates_counterpart(
        self,
        user_cls,
        get_social_settings,
        get_setting,
        get_profile_model_cls,
        ensure_counterpart,
    ):
        identity = SocialIdentity(
            provider="google",
            provider_user_id="social-1",
            email="host@example.com",
            email_verified=True,
            first_name="Host",
            last_name_1="User",
        )
        get_social_settings.return_value = {
            "REQUIRE_VERIFIED_EMAIL": True,
        }
        get_setting.side_effect = lambda key: {
            "TERMS_AND_CONDITIONS_REQUIRED": False,
            "DEFAULT_PROFILE_ROLE": "GUEST",
        }[key]

        user = MagicMock()
        user_cls.objects.create_user.return_value = user
        user_cls.objects.filter.return_value.exists.return_value = False

        profile = MagicMock()
        profile_model = MagicMock()
        profile_model.objects.create.return_value = profile
        get_profile_model_cls.return_value = profile_model

        SocialAuthService._create_user_from_identity(identity, terms_accepted=True, role="HOST")

        ensure_counterpart.assert_called_once_with(profile, create_missing=True)

    @patch("jb_drf_auth.services.login.ProfileRoleMirrorService.autocure_for_profile")
    @patch("jb_drf_auth.services.login.ClientService.response_for_client")
    @patch("jb_drf_auth.services.login.TokensService.get_tokens_for_user")
    @patch("jb_drf_auth.services.login.EmailOrUsernameModelBackend.authenticate")
    def test_basic_login_autocures_counterpart(
        self,
        authenticate,
        get_tokens_for_user,
        response_for_client,
        autocure_for_profile,
    ):
        profile = MagicMock()
        user = MagicMock()
        user.is_verified = True
        user.is_active = True
        user.deleted = None
        user.get_default_profile.return_value = profile
        authenticate.return_value = user

        get_tokens_for_user.return_value = {"access": "a"}
        response_for_client.return_value = {"ok": True}

        LoginService.basic_login("host@example.com", "secret", "web", None)

        autocure_for_profile.assert_called_once_with(profile)

    @patch("jb_drf_auth.services.login.ProfileRoleMirrorService.autocure_for_profile")
    @patch("jb_drf_auth.services.login.ClientService.response_for_client")
    @patch("jb_drf_auth.services.login.TokensService.get_tokens_for_user")
    def test_switch_profile_autocures_counterpart(
        self,
        get_tokens_for_user,
        response_for_client,
        autocure_for_profile,
    ):
        profile = MagicMock()
        queryset = MagicMock()
        queryset.get.return_value = profile

        profiles_manager = MagicMock()
        profiles_manager.filter.return_value = queryset
        profiles_manager.model = SimpleNamespace(
            _meta=SimpleNamespace(get_fields=lambda: []),
            DoesNotExist=Exception,
        )

        user = MagicMock()
        user.profiles = profiles_manager

        get_tokens_for_user.return_value = {"access": "a"}
        response_for_client.return_value = {"ok": True}

        LoginService.switch_profile(user, profile_id=5, client="web", device_data=None)

        autocure_for_profile.assert_called_once_with(profile)

    @patch("jb_drf_auth.services.me.ProfileRoleMirrorService.autocure_for_profile")
    @patch("jb_drf_auth.services.me.MeService.get_me_web")
    @patch("jb_drf_auth.services.me.get_profile_model_cls")
    def test_me_autocures_counterpart(
        self,
        get_profile_model_cls,
        get_me_web,
        autocure_for_profile,
    ):
        profile = MagicMock()
        profile_model = MagicMock()
        profile_model.objects.get.return_value = profile
        get_profile_model_cls.return_value = profile_model
        get_me_web.return_value = {"ok": True}

        user = SimpleNamespace()
        MeService.get_me(user=user, client="web", profile_id=10)

        autocure_for_profile.assert_called_once_with(profile)

    @patch("jb_drf_auth.services.magic_link.ProfileRoleMirrorService.autocure_for_profile")
    @patch("jb_drf_auth.services.magic_link.MagicLinkService._mark_patient_invite_consumed")
    @patch("jb_drf_auth.services.magic_link.ClientService.response_for_client")
    @patch("jb_drf_auth.services.magic_link.TokensService.get_tokens_for_user")
    @patch("jb_drf_auth.services.magic_link.MagicLinkService._resolve_profile")
    @patch("jb_drf_auth.services.magic_link.User")
    @patch("jb_drf_auth.services.magic_link.cache.add")
    @patch("jb_drf_auth.services.magic_link.signing.loads")
    @patch("jb_drf_auth.services.magic_link.MagicLinkService._ttl_seconds")
    def test_magic_link_consume_autocures_counterpart(
        self,
        ttl_seconds,
        signing_loads,
        cache_add,
        user_cls,
        resolve_profile,
        get_tokens_for_user,
        response_for_client,
        mark_patient_invite_consumed,
        autocure_for_profile,
    ):
        ttl_seconds.return_value = 900
        signing_loads.return_value = {"jti": "token-1", "sub": 1}
        cache_add.return_value = True

        user = MagicMock()
        user.id = 1
        user.is_active = True
        user.deleted = None
        user_cls.objects.filter.return_value.first.return_value = user

        profile = MagicMock()
        profile.role = "HOST"
        resolve_profile.return_value = profile

        get_tokens_for_user.return_value = {"access": "a"}
        response_for_client.return_value = {"ok": True}

        MagicLinkService.consume_token(token="signed-token", client="web")

        autocure_for_profile.assert_called_once_with(profile)
        mark_patient_invite_consumed.assert_called_once()

    @patch("jb_drf_auth.serializers.profile.ProfileRoleMirrorService.ensure_counterpart")
    @patch("jb_drf_auth.serializers.profile.serializers.ModelSerializer.create")
    def test_profile_serializer_create_ensures_counterpart(
        self,
        super_create,
        ensure_counterpart,
    ):
        user = SimpleNamespace(is_authenticated=True)
        request = SimpleNamespace(user=user)
        profile = SimpleNamespace(user=user)
        super_create.return_value = profile

        serializer = ProfileSerializer(context={"request": request})
        serializer.create({"first_name": "Host"})

        ensure_counterpart.assert_called_once_with(profile, create_missing=True)

    @patch("jb_drf_auth.serializers.profile.ProfileRoleMirrorService.sync_profile")
    @patch("jb_drf_auth.serializers.profile.serializers.ModelSerializer.update")
    def test_profile_serializer_update_syncs_allowed_fields(
        self,
        super_update,
        sync_profile,
    ):
        user = SimpleNamespace(is_authenticated=True)
        request = SimpleNamespace(user=user)
        instance = SimpleNamespace(user=user)
        super_update.return_value = instance

        serializer = ProfileSerializer(context={"request": request})
        serializer.update(instance, {"first_name": "Nuevo", "birthday": "1990-01-01"})

        sync_profile.assert_called_once_with(
            instance,
            changed_fields={"first_name", "birthday"},
        )

    @patch("jb_drf_auth.serializers.profile.ProfileRoleMirrorService.sync_profile")
    @patch("jb_drf_auth.serializers.profile.optimize_profile_picture")
    def test_profile_picture_update_syncs_picture(
        self,
        optimize_profile_picture,
        sync_profile,
    ):
        optimized = MagicMock()
        optimize_profile_picture.return_value = optimized

        profile = MagicMock()
        serializer = ProfilePictureUpdateSerializer(context={"request": SimpleNamespace(user=MagicMock())})
        serializer._validated_data = {"picture": MagicMock()}

        with patch.object(serializer, "_resolve_profile", return_value=profile):
            serializer.save()

        self.assertEqual(profile.picture, optimized)
        profile.save.assert_called_once()
        sync_profile.assert_called_once_with(profile, changed_fields={"picture"})
