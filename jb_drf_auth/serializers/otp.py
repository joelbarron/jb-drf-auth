from rest_framework import serializers

from jb_drf_auth.conf import get_setting
from jb_drf_auth.serializers.device import DevicePayloadSerializer


CLIENT_CHOICES = get_setting("CLIENT_CHOICES")
OTP_LENGTH = get_setting("OTP_LENGTH")


class OtpCodeRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    channel = serializers.ChoiceField(choices=[("email", "Email"), ("sms", "SMS")])

    def validate(self, data):
        if not data.get("email") and not data.get("phone"):
            raise serializers.ValidationError("Debes proporcionar un email o un telefono.")
        return data


class OtpCodeVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    code = serializers.CharField(min_length=OTP_LENGTH, max_length=OTP_LENGTH)
    client = serializers.ChoiceField(choices=CLIENT_CHOICES)
    device = DevicePayloadSerializer(write_only=True, required=False)

    def validate(self, data):
        if not data.get("email") and not data.get("phone"):
            raise serializers.ValidationError("Debes proporcionar un email o un telefono.")
        return data
