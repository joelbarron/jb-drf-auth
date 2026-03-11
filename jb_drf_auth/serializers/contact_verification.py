from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from jb_drf_auth.conf import get_setting

OTP_LENGTH = int(get_setting("OTP_LENGTH") or 6)


class ContactVerificationRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    channel = serializers.ChoiceField(choices=[("email", "Email"), ("sms", "SMS")])

    def validate(self, data):
        email = data.get("email")
        phone = data.get("phone")
        channel = data.get("channel")

        if not email and not phone:
            raise serializers.ValidationError(_("Debes proporcionar un email o un teléfono."))
        if channel == "email" and not email:
            raise serializers.ValidationError({"email": _("Debes proporcionar un email para verificar.")})
        if channel == "sms" and not phone:
            raise serializers.ValidationError({"phone": _("Debes proporcionar un teléfono para verificar.")})
        return data


class ContactVerificationVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    channel = serializers.ChoiceField(choices=[("email", "Email"), ("sms", "SMS")])
    code = serializers.CharField(min_length=OTP_LENGTH, max_length=OTP_LENGTH)

    def validate(self, data):
        email = data.get("email")
        phone = data.get("phone")
        channel = data.get("channel")

        if not email and not phone:
            raise serializers.ValidationError(_("Debes proporcionar un email o un teléfono."))
        if channel == "email" and not email:
            raise serializers.ValidationError({"email": _("Debes proporcionar un email para verificar.")})
        if channel == "sms" and not phone:
            raise serializers.ValidationError({"phone": _("Debes proporcionar un teléfono para verificar.")})
        return data
