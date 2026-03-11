from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from jb_drf_auth.conf import get_setting, get_social_settings
from jb_drf_auth.serializers.device import DevicePayloadSerializer
from jb_drf_auth.services.social_auth import SocialAuthService


CLIENT_CHOICES = get_setting("CLIENT_CHOICES")


class SocialLoginSerializer(serializers.Serializer):
    provider = serializers.CharField()
    id_token = serializers.CharField(required=False, allow_blank=True)
    access_token = serializers.CharField(required=False, allow_blank=True)
    authorization_code = serializers.CharField(required=False, allow_blank=True)
    redirect_uri = serializers.CharField(required=False, allow_blank=True)
    code_verifier = serializers.CharField(required=False, allow_blank=True)
    client_id = serializers.CharField(required=False, allow_blank=True)
    client = serializers.ChoiceField(choices=CLIENT_CHOICES)
    device = DevicePayloadSerializer(write_only=True, required=False)
    role = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    terms_and_conditions_accepted = serializers.BooleanField(required=False, default=False)

    def validate_provider(self, value):
        providers = get_social_settings().get("PROVIDERS", {})
        if value not in providers:
            raise serializers.ValidationError(_("Unsupported social provider."))
        return value

    def validate(self, data):
        provider = data.get("provider")
        if provider in ("google", "apple"):
            if not data.get("id_token") and not data.get("authorization_code"):
                raise serializers.ValidationError(
                    {"detail": _("id_token or authorization_code is required for this provider.")}
                )
            if data.get("authorization_code"):
                if not data.get("redirect_uri"):
                    raise serializers.ValidationError(
                        {"detail": _("redirect_uri is required for authorization_code flow.")}
                    )
                if not data.get("client_id"):
                    raise serializers.ValidationError(
                        {"detail": _("client_id is required for authorization_code flow.")}
                    )
        if provider == "facebook" and not data.get("access_token"):
            raise serializers.ValidationError({"detail": _("access_token is required for Facebook.")})
        return data

    def save(self, **kwargs):
        payload = {
            "id_token": self.validated_data.get("id_token"),
            "access_token": self.validated_data.get("access_token"),
            "authorization_code": self.validated_data.get("authorization_code"),
            "redirect_uri": self.validated_data.get("redirect_uri"),
            "code_verifier": self.validated_data.get("code_verifier"),
            "client_id": self.validated_data.get("client_id"),
        }
        return SocialAuthService.login_or_register(
            provider_name=self.validated_data.get("provider"),
            payload=payload,
            client=self.validated_data.get("client"),
            device_data=self.validated_data.get("device"),
            role=self.validated_data.get("role"),
            terms_and_conditions_accepted=self.validated_data.get(
                "terms_and_conditions_accepted", False
            ),
        )


class SocialLinkSerializer(serializers.Serializer):
    provider = serializers.CharField()
    id_token = serializers.CharField(required=False, allow_blank=True)
    access_token = serializers.CharField(required=False, allow_blank=True)
    authorization_code = serializers.CharField(required=False, allow_blank=True)
    redirect_uri = serializers.CharField(required=False, allow_blank=True)
    code_verifier = serializers.CharField(required=False, allow_blank=True)
    client_id = serializers.CharField(required=False, allow_blank=True)

    def validate_provider(self, value):
        providers = get_social_settings().get("PROVIDERS", {})
        if value not in providers:
            raise serializers.ValidationError(_("Unsupported social provider."))
        return value

    def validate(self, data):
        provider = data.get("provider")
        if provider in ("google", "apple"):
            if not data.get("id_token") and not data.get("authorization_code"):
                raise serializers.ValidationError(
                    {"detail": _("id_token or authorization_code is required for this provider.")}
                )
            if data.get("authorization_code"):
                if not data.get("redirect_uri"):
                    raise serializers.ValidationError(
                        {"detail": _("redirect_uri is required for authorization_code flow.")}
                    )
                if not data.get("client_id"):
                    raise serializers.ValidationError(
                        {"detail": _("client_id is required for authorization_code flow.")}
                    )
        if provider == "facebook" and not data.get("access_token"):
            raise serializers.ValidationError({"detail": _("access_token is required for Facebook.")})
        return data

    def save(self, **kwargs):
        payload = {
            "id_token": self.validated_data.get("id_token"),
            "access_token": self.validated_data.get("access_token"),
            "authorization_code": self.validated_data.get("authorization_code"),
            "redirect_uri": self.validated_data.get("redirect_uri"),
            "code_verifier": self.validated_data.get("code_verifier"),
            "client_id": self.validated_data.get("client_id"),
        }
        return SocialAuthService.link_account(
            user=self.context["request"].user,
            provider_name=self.validated_data.get("provider"),
            payload=payload,
        )


class SocialUnlinkSerializer(serializers.Serializer):
    provider = serializers.CharField()

    def validate_provider(self, value):
        providers = get_social_settings().get("PROVIDERS", {})
        if value not in providers:
            raise serializers.ValidationError(_("Unsupported social provider."))
        return value

    def save(self, **kwargs):
        return SocialAuthService.unlink_account(
            user=self.context["request"].user,
            provider_name=self.validated_data.get("provider"),
        )
