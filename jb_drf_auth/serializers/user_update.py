from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from jb_drf_auth.services.contact_verification import ContactVerificationService


def _normalize_contact_value(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip()
    return value


def validate_contact_change_proofs(instance, attrs):
    email_new = _normalize_contact_value(attrs.get("email", serializers.empty))
    phone_new = _normalize_contact_value(attrs.get("phone", serializers.empty))

    email_changed = email_new is not serializers.empty and email_new != _normalize_contact_value(getattr(instance, "email", None))
    phone_changed = phone_new is not serializers.empty and phone_new != _normalize_contact_value(getattr(instance, "phone", None))

    if email_changed and email_new:
        email_proof = attrs.get("email_verification_proof_token")
        if not email_proof:
            raise serializers.ValidationError(
                {"email_verification_proof_token": _("Debes validar el correo con OTP antes de guardarlo.")}
            )
        ContactVerificationService.verify_proof_token(
            email_proof,
            user_id=instance.pk,
            channel="email",
            email=email_new,
        )

    if phone_changed and phone_new:
        phone_proof = attrs.get("phone_verification_proof_token")
        if not phone_proof:
            raise serializers.ValidationError(
                {"phone_verification_proof_token": _("Debes validar el teléfono con OTP antes de guardarlo.")}
            )
        ContactVerificationService.verify_proof_token(
            phone_proof,
            user_id=instance.pk,
            channel="sms",
            phone=phone_new,
        )


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ()

    def get_fields(self):
        allowed = ("email", "username", "phone", "terms_and_conditions")
        model_field_names = {field.name for field in self.Meta.model._meta.get_fields()}
        self.Meta.fields = tuple(field for field in allowed if field in model_field_names)
        fields = super().get_fields()
        fields["language"] = serializers.CharField(required=False, allow_blank=False)
        fields["timezone"] = serializers.CharField(required=False, allow_blank=False)
        fields["email_verification_proof_token"] = serializers.CharField(
            required=False,
            allow_blank=False,
            write_only=True,
        )
        fields["phone_verification_proof_token"] = serializers.CharField(
            required=False,
            allow_blank=False,
            write_only=True,
        )
        return fields

    def validate_email(self, value):
        user_model = self.Meta.model
        instance = self.instance
        if value and user_model.objects.filter(email=value).exclude(pk=instance.pk).exists():
            raise serializers.ValidationError(_("Ya existe un usuario con este correo."))
        return value

    def validate_username(self, value):
        user_model = self.Meta.model
        instance = self.instance
        if value and user_model.objects.filter(username=value).exclude(pk=instance.pk).exists():
            raise serializers.ValidationError(_("El nombre de usuario ya está en uso."))
        return value

    def validate_phone(self, value):
        user_model = self.Meta.model
        instance = self.instance
        if value and user_model.objects.filter(phone=value).exclude(pk=instance.pk).exists():
            raise serializers.ValidationError(_("El teléfono ya está en uso."))
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        validate_contact_change_proofs(self.instance, attrs)
        return attrs

    def update(self, instance, validated_data):
        language = validated_data.pop("language", None)
        timezone = validated_data.pop("timezone", None)
        validated_data.pop("email_verification_proof_token", None)
        validated_data.pop("phone_verification_proof_token", None)

        instance = super().update(instance, validated_data)

        if language is not None or timezone is not None:
            payload = instance.settings if isinstance(instance.settings, dict) else {}
            if language is not None:
                payload["language"] = language
            if timezone is not None:
                payload["timezone"] = timezone
            instance.settings = payload
            instance.save(update_fields=["settings"])

        return instance
