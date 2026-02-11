from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from jb_drf_auth.services.password_reset import PasswordResetService


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self):
        return PasswordResetService.send_reset_email(
            self.validated_data["email"], raise_on_fail=False
        )


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError(_("Las contrasenas no coinciden."))
        return data

    def save(self):
        success = PasswordResetService.reset_password(
            uidb64=self.validated_data["uid"],
            token=self.validated_data["token"],
            new_password=self.validated_data["new_password"],
        )
        if not success:
            raise serializers.ValidationError(_("Token invalido o expirado."))


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError(_("Las contrasenas no coinciden."))
        return data

    def save(self, **kwargs):
        user = self.context["request"].user
        success = PasswordResetService.change_password(
            user=user,
            old_password=self.validated_data["old_password"],
            new_password=self.validated_data["new_password"],
        )
        if not success:
            raise serializers.ValidationError({"old_password": _("Contrasena actual incorrecta.")})
