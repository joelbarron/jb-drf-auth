from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from jb_drf_auth.services.email_confirmation import EmailConfirmationService


User = get_user_model()


class EmailConfirmationSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()

    def validate(self, data):
        try:
            uid = urlsafe_base64_decode(data["uid"]).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError(_("Enlace invalido."))

        if not default_token_generator.check_token(user, data["token"]):
            raise serializers.ValidationError(_("El token es invalido o ha expirado."))
        data["user"] = user
        return data

    def save(self):
        user = self.validated_data["user"]
        user.is_active = True
        user.is_verified = True
        user.save()
        return user


class ResendConfirmationEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(_("No existe un usuario con este correo."))

        if user.is_active:
            raise serializers.ValidationError(_("El correo ya fue verificado."))

        self.context["user"] = user
        return value

    def save(self):
        user = self.context["user"]
        return EmailConfirmationService.send_verification_email(user, raise_on_fail=False)
