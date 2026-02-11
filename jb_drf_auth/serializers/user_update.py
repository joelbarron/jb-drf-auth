from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


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
            raise serializers.ValidationError(_("El nombre de usuario ya esta en uso."))
        return value

    def validate_phone(self, value):
        user_model = self.Meta.model
        instance = self.instance
        if value and user_model.objects.filter(phone=value).exclude(pk=instance.pk).exists():
            raise serializers.ValidationError(_("El telefono ya esta en uso."))
        return value

    def update(self, instance, validated_data):
        language = validated_data.pop("language", None)
        timezone = validated_data.pop("timezone", None)

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
