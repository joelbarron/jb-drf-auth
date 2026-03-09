from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from jb_drf_auth.conf import get_setting
from jb_drf_auth.serializers.device import DevicePayloadSerializer


CLIENT_CHOICES = get_setting("CLIENT_CHOICES")


class MagicLinkConsumeSerializer(serializers.Serializer):
    token = serializers.CharField()
    client = serializers.ChoiceField(choices=CLIENT_CHOICES, default="web")
    role = serializers.CharField(required=False, allow_blank=True)
    device = DevicePayloadSerializer(write_only=True, required=False)

    def validate_token(self, value):
        token = str(value or "").strip()
        if not token:
            raise serializers.ValidationError(_("Debes proporcionar un token válido."))
        return token
