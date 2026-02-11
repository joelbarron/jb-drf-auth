"""Register serializer."""

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from jb_drf_auth.conf import get_setting
from jb_drf_auth.services.register import RegisterService


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(min_length=8, max_length=128)
    password_confirm = serializers.CharField(min_length=8, max_length=128)
    first_name = serializers.CharField(max_length=100)
    last_name_1 = serializers.CharField(max_length=150)
    last_name_2 = serializers.CharField(max_length=150, required=False, allow_blank=True, allow_null=True)
    birthday = serializers.DateField(required=True)
    gender = serializers.CharField(max_length=50)
    role = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    terms_and_conditions_accepted = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        if get_setting("TERMS_AND_CONDITIONS_REQUIRED") and not attrs.get(
            "terms_and_conditions_accepted", False
        ):
            raise serializers.ValidationError(
                {"terms_and_conditions_accepted": _("Debes aceptar terminos y condiciones.")}
            )
        return attrs

    def create(self, validated_data):
        user, email_sent = RegisterService.register_user(
            email=validated_data["email"],
            username=validated_data.get("username"),
            password=validated_data["password"],
            password_confirm=validated_data["password_confirm"],
            first_name=validated_data["first_name"],
            last_name_1=validated_data["last_name_1"],
            last_name_2=validated_data.get("last_name_2"),
            birthday=validated_data["birthday"],
            gender=validated_data["gender"],
            role=validated_data.get("role"),
            terms_and_conditions_accepted=validated_data.get(
                "terms_and_conditions_accepted", False
            ),
        )
        self.email_sent = email_sent
        return user
